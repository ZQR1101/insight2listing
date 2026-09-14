# Insight2Listing

Evidence-grounded market insight, product opportunity validation, and intelligent Listing workflows for Amazon US.

> This repository is scaffolded only. Product features are not implemented yet.

## Current scope

- Amazon US first
- Workflow-first UI with chat as an assistant
- CSV, JSON, and XLSX import architecture
- Self-hosted first, hosted-ready
- BYOK model usage: users provide their own model API key
- GPT Image 2 planned for product image generation and editing
- MIT licensed source code

The initial test products are compression packing cubes, glass oil sprayers, and car trash cans. Amazon seller authorization and production SP-API integration are deferred to a later beta phase.

## Documentation

- [中文详细产品与技术方案](outputs/Insight2Listing详细产品与技术方案.md)
- [English project guide](README.en.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Data and asset licensing](DATA_LICENSE.md)

## Local setup

The initial repository contains structure and documentation only. Runtime setup will be added in a later implementation phase.

```powershell
Copy-Item .env.example .env
docker compose up -d
```

Do not commit `.env` or any API key. The API key must remain on the backend, never in browser code.

## License

Source code is released under the MIT License. Third-party datasets, images, trademarks, and user-uploaded content are not automatically covered by this license.
