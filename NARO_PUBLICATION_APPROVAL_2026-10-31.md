> Published and verified: [NARO v0.1.0](https://github.com/JLuethe/naro/releases/tag/v0.1.0).
> See the [publication record](NARO_RELEASE_PUBLICATION_2026-10-31.md).
> The preparation and approval text below is retained as historical context.

# NARO 0.1.0 — publication approval

Publication preflight passed. No tag, asset upload or public release was created.

## Exact action awaiting approval

- Destination: https://github.com/JLuethe/naro
- Create and push annotated tag `v0.1.0` at `6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50`.
- Create a public **GitHub prerelease**, with latest disabled.
- Title: **NARO 0.1.0 — experimental Linux x86_64 release**.
- Use the [prepared release description](docs/release-v0.1.0-save-hardening-review-2026-10-31/RELEASE_BODY.md) unchanged.
- Upload exactly the seven files below, publishing binary and matching source together.
- Download all public assets anonymously and verify every size/hash, SHA256SUMS, tag resolution and documentation links.
- Community announcements are outside this approval.

## Exact files

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `BUILD-ENVIRONMENT.json` | 10039 | `c108bd27258f15e9bc1d679ab25cc7c78f770a3703a4c6f3fc6612ad29350935` |
| `QUALIFICATION.json` | 23003 | `55431b7f7b0e8da96ff8224c75b999d13e818550ff240606be37efb9ae2e0ce3` |
| `RUNTIME-REQUIREMENTS.md` | 3734 | `7bc65b15d0c290fe9a3bd6f41b24e7e822ec580a936496f2019be5a524592433` |
| `SHA256SUMS` | 541 | `d6ceb5f7b73862d35ad34eb5715dca73bd218ceba668a85e9901b8bacd18d228` |
| `build.json` | 198965 | `cbe187075e192cf64cc83ca1994686c6244cd0f73bfd623b72e815df82814f46` |
| `naro-0.1.0-source.tar.gz` | 3876132 | `062b8f73b3d6aaa6b32f421a0cc182e142804ea8b6c295a01af707c8023362be` |
| `naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz` | 2702797 | `3d6b4d4f67fa97060993d31f4e75b6a83f65f52a465ce3efaf7334dead42179f` |

Release description SHA-256: `b1cfd14f02b8e91069ccbd64ea7ff8b334b59abaad04b3daa2644e539ddbbdcd`.

Working and preserved copies match the [asset manifest](docs/release-v0.1.0-save-hardening-review-2026-10-31/asset-manifest.json). The verified Ubuntu executable and source archives will be reused.

## Completed publication preflight

- Production, packaging/tag-target and final review-delivery CI were rechecked live and all succeeded.
- Main is at `35d2a2f7a8c7bd8adc832e13bc31ec74f3e1d2b9`; tracked state is clean.
- Release/tag absence checked before publication attempt.
- Frozen inputs, production fingerprint, archived executable and all seven working/backup files verified.
- Release description matches its reviewed checksum.

## Why explicit approval is needed

Automatic approval review rejected the attempted publication command. It determined that "start doing things to get this release going" did not explicitly approve this exact tag, artifact set, destination and public publication side effect after the earlier reservation of publication for explicit approval. The command did not execute. No workaround was attempted.

A sufficient approval is: **Approve publishing NARO v0.1.0 to JLuethe/naro as the experimental prerelease described in this packet, with these seven files.**

After approval, recheck mutable remote state before execution, stage and verify the uploaded files, publish, and verify the public downloads. Record the release URL and asset IDs; then update candidate documentation with the verified public URL.
