#ifndef DEADLETTER_WORN_FORWARD_INCLUDED
#define DEADLETTER_WORN_FORWARD_INCLUDED

// The prototype's worn paint (index.html L386–L391 NOISE, L509–L519 wornMaterial; port_architecture §4.3), one to one:
// object-space value-noise fbm blends the base colour to dirt (grime and vertical streaks), then to chipped paint with its
// own roughness, then to dust on up-facing surfaces. Parameters come from Core's PrototypeMaterials.Worn, set by
// ArtMaterials as raw linear vectors (SetVector: no sRGB conversion, like three.js's lin()).
// Included after URP's LitForwardPass.hlsl; WornPassFragment is LitPassFragment with ApplyWorn after the surface data.
// The worn parameters live outside UnityPerMaterial, so the shader is not SRP-batcher compatible yet (U-15 tiers).

float4 _WornDirt;     // rgb
float4 _WornChip;     // rgb
float4 _WornDust;     // rgb
float4 _WornParams;   // grime scale, chip scale, chip amount, chip roughness
float4 _WornParams2;  // dust amount, streak amount

float WornHash13(float3 p)
{
    p = frac(p * 0.1031);
    p += dot(p, p.zyx + 31.32);
    return frac((p.x + p.y) * p.z);
}

float WornNoise(float3 p)
{
    float3 i = floor(p);
    float3 f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    return lerp(lerp(lerp(WornHash13(i), WornHash13(i + float3(1, 0, 0)), f.x),
                     lerp(WornHash13(i + float3(0, 1, 0)), WornHash13(i + float3(1, 1, 0)), f.x), f.y),
                lerp(lerp(WornHash13(i + float3(0, 0, 1)), WornHash13(i + float3(1, 0, 1)), f.x),
                     lerp(WornHash13(i + float3(0, 1, 1)), WornHash13(i + float3(1, 1, 1)), f.x), f.y), f.z);
}

float WornFbm(float3 p)
{
    float a = 0.5, s = 0.0;
    [unroll] for (int i = 0; i < 3; i++) { s += a * WornNoise(p); p *= 2.03; a *= 0.5; }
    return s / 0.875;
}

// objPos: the mesh's own coordinates (the prototype's vObjPos = position; the region generators build meshes in world
// space, so static batching changes nothing). normalWS: the world normal (the prototype's worldN).
void ApplyWorn(float3 objPos, float3 normalWS, inout SurfaceData s)
{
    float grimeM = smoothstep(0.44, 0.66, WornFbm(objPos * _WornParams.x));
    float streakM = smoothstep(0.52, 0.72, WornFbm(objPos * float3(9.0, 1.1, 9.0) + 11.0)) * _WornParams2.y;
    s.albedo = lerp(s.albedo, _WornDirt.rgb, saturate(max(grimeM, streakM)));
    float chipM = smoothstep(_WornParams.z, _WornParams.z + 0.015, WornFbm(objPos * _WornParams.y + 7.3));
    s.albedo = lerp(s.albedo, _WornChip.rgb, chipM);
    s.smoothness = lerp(s.smoothness, 1.0 - _WornParams.w, chipM);   // roughnessFactor = mix(rough, chipRough, chipM)
    float dustM = smoothstep(0.35, 0.9, normalWS.y) * smoothstep(0.35, 0.7, WornNoise(objPos * 14.0)) * _WornParams2.x;
    s.albedo = lerp(s.albedo, _WornDust.rgb, dustM);
}

void WornPassFragment(
    Varyings input
    , out half4 outColor : SV_Target0
#ifdef _WRITE_RENDERING_LAYERS
    , out uint outRenderingLayers : SV_Target1
#endif
)
{
    UNITY_SETUP_INSTANCE_ID(input);
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

    SurfaceData surfaceData;
    InitializeStandardLitSurfaceData(input.uv, surfaceData);
    ApplyWorn(TransformWorldToObject(input.positionWS), normalize(input.normalWS), surfaceData);

#ifdef LOD_FADE_CROSSFADE
    LODFadeCrossFade(input.positionCS);
#endif

    InputData inputData;
    InitializeInputData(input, surfaceData.normalTS, inputData);
    SETUP_DEBUG_TEXTURE_DATA(inputData, UNDO_TRANSFORM_TEX(input.uv, _BaseMap));

#if defined(_DBUFFER)
    ApplyDecalToSurfaceData(input.positionCS, surfaceData, inputData);
#endif

    InitializeBakedGIData(input, inputData);

    half4 color = UniversalFragmentPBR(inputData, surfaceData);
    color.rgb = MixFog(color.rgb, inputData.fogCoord);
    color.a = OutputAlpha(color.a, IsSurfaceTypeTransparent());

    outColor = color;

#ifdef _WRITE_RENDERING_LAYERS
    outRenderingLayers = EncodeMeshRenderingLayer();
#endif
}

#endif
