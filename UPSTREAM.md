# Upstream

Konnect v0.13.0, commit 6bbe3e4f890ba1d37c0e5d5f38ccd03d90958c9e.
Source: https://github.com/mixelpixx/Konnect/tree/v0.13.0
License: AGPL-3.0, reproduced in LICENSE. Konnect remains unmodified.
Linux amd64 release archive SHA-256:
`9c9d28e7d905d8e8519339a78890193f252bc8134993349b40d80e3a67b93512`.
Dockerfile verifies this checksum before installing the amd64 binary. Konnect
does not publish a Linux arm64 binary for v0.13.0, so the arm64 image builds the
same commit from the vendored, unmodified source with its pinned Rust toolchain.
Matching source is retained under vendor/Konnect, excluding Git metadata.
FreeRouting v2.3.0 is installed from its architecture-independent release JAR.
JAR SHA-256:
`3cf18d608437740bc497db6b8ef5888e2e60a08de0def20691d1bad0c0e0ee24`.
It runs on the multi-architecture Eclipse Temurin Java 25 runtime.
KiCad and standard symbol/footprint libraries come from official KiCad 10.0
release PPA on Ubuntu 24.04. Package versions are recorded by acceptance.
Standard 3D model library is omitted due to size. Supply project models separately.
