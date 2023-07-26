#!/usr/bin/env bash
#
# Extracts platform-specific TAR archives
# containing static executables from the OCI image,
# and publishes them in a GitHub release.

set -euxo pipefail

IMAGE=$1

dist_dir="$(pwd)/dist"
rm -rf "${dist_dir}"
mkdir -p "${dist_dir}"

archive_base="${dist_dir}/sfkit_"
sfkit_dir="sfkit/"

platforms=$(
    docker buildx imagetools inspect "${IMAGE}" \
        --format '{{range .Manifest.Manifests}}{{with .Platform}}{{if (ne .OS "unknown")}}  {{.OS}}/{{.Architecture}}{{if .Variant}}/{{.Variant}}{{end}}{{end}}{{end}}{{end}}'
)
for p in ${platforms} ; do
    (
        tmp_dir=$(mktemp -d)
        pushd "${tmp_dir}"

        crane export "${IMAGE}" - --platform "$p" | tar -xf - "${sfkit_dir}"
        tar -czf "${archive_base}${p//\//_}.tar.gz" "${sfkit_dir}"

        popd
        rm -rf "${tmp_dir}"
    ) &
done
wait

last_release=$(gh release list -L 1 | awk '{print $3}')
next_release=$(perl -pe 's/(\d+)$/($1+1)/e' <<< "${last_release}")

gh release create --generate-notes \
    --notes-start-tag "${last_release}" "${next_release}" "install.sh" "${archive_base}"*

rm -rf "${dist_dir}"
