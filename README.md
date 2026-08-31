<div align="center">

<h3><code>$ cat contributions.log</code></h3>
<img src="./graph.svg" width="820" />

<br><br>

<h3><code>$ whoami --verbose</code></h3>

<table>
  <tr>
    <td valign="top"><img src="./portrait.svg" width="360" /></td>
    <td valign="top"><img src="./sysinfo.svg" width="540" /></td>
  </tr>
</table>

<br>

<h3><code>$ ls projects/ --pinned</code></h3>

| Project | What it does | Stack |
|---|---|---|
| [RP Vision AI](https://github.com/PrakashWebDevX/RPVisionAI-Tool) | Text-to-image generator | React, Node.js |
| [AI Business Research Agent](https://github.com/PrakashWebDevX/AI-Business-Research-Agent-Backend) | Autonomous agent routing between SQL + live web search | Python, LangChain, RAG |
| [PulseChat](https://github.com/PrakashWebDevX/pulsechat-frontend) | Real-time chat frontend | TypeScript |
| [PR TECH Agency](https://prtech.netlify.app/) | Web design & AI solutions agency site | Custom |

</div>

<!--
  How this works:
  - GitHub strips <script> tags and most inline CSS from markdown, but
    an <img> pointing at a local .svg is just rendered as an image —
    and that image is free to animate itself via SMIL / embedded <style>.
  - portrait.svg / sysinfo.svg / graph.svg are all generated locally by
    the scripts in tools/, then committed as flat files.
  - Only graph.svg needs to change day to day, so the GitHub Actions
    workflow (.github/workflows/refresh-graph.yml) re-pulls contribution
    data and re-renders just that file once a day.
  - To rebuild the portrait after swapping in a new photo:
      python -m venv .venv && source .venv/bin/activate
      pip install -r tools/requirements-art.txt
      python tools/clean_photo.py my-photo.jpg
      python tools/render_portrait.py
  - To rebuild the info panel after editing tools/render_panel.py:
      python tools/render_panel.py
-->
