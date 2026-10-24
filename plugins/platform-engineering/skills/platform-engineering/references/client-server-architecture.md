# Client-Server Architecture

Identify the authoritative trust boundary for each decision. Untrusted clients may calculate previews and own local behavior, but remote protected actions require enforcement at the trusted server/core boundary. Offline or local applications need their actual authority model; the presence of business logic in a client is not by itself a defect.

## MUST

- **Never place authorization or business-rule enforcement solely on the client.** All client platforms are reverse-engineerable. JavaScript in SPAs/PWAs is fully readable; mobile APKs can be decompiled; Electron apps bundle readable Node.js code.

## DO

- Use a **Backend-for-Frontend (BFF) pattern** when different platforms need different data shapes, rather than duplicating business logic across clients.
- For desktop apps, treat the renderer process as untrusted and route all sensitive operations through the main/core process that communicates with the server.

## DON'T

- Duplicate business logic across SPA, mobile, and desktop clients. Consistency bugs emerge when pricing or eligibility rules diverge between platforms.
- Trust client-computed values without server re-validation.
