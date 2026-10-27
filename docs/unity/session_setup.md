# Cloud session setup

Claude cloud sessions can't run the Unity editor (the proxy blocks Unity's download hosts), which is why
`DeadLetter.Core` is pure C# (issue #1). Everything else a session needs installs through the proxy:

| Tool | For | How |
|---|---|---|
| dotnet 8 SDK | building and testing `DeadLetter.Core` | `apt-get install -y dotnet-sdk-8.0` (Ubuntu 24.04's repos; dot.net's own hosts are blocked) |
| bpy (Blender 5.2 as a Python module) | running the `art/**` generators headless | `python3 -m pip install --break-system-packages bpy` (large; only when needed) |

`tools/setup/cloud_session.sh` does both: dotnet always, bpy only with `DL_NEEDS_BLENDER=1`. It's idempotent and
takes about 0.2 s once the tools are there (about 17 s to install dotnet).

- **Once per account:** paste `bash tools/setup/cloud_session.sh` into the cloud environment's **Setup script**
  (the environment menu in the session's title bar, then Edit). New sessions then start with the tools. Add
  `DL_NEEDS_BLENDER=1` to the environment's variables if that account works on art.
- **Otherwise:** run it by hand at the start of a session.

Checked 26 Oct 2026: `dotnet new xunit` + `dotnet test` restores from NuGet through the proxy and passes.
