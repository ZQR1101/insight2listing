# Security

Please do not report secrets or vulnerabilities in public issues. Use a private security contact when one is configured for the repository.

Never commit:

- OpenAI or Amazon credentials;
- Seller Central login data;
- private customer or review exports;
- unlicensed product images;
- production database dumps.

The application is designed to keep model keys on the backend. Local users should configure them through environment variables or a secret manager.
