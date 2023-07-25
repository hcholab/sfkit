#!/usr/bin/env bash
#
# Extracts platform-specific TAR archives
# containing static executables from the OCI image,
# and publishes them in a GitHub release.

set -euxo pipefail

IMAGE=$1

last_release=$(gh release list -L 1 | awk '{print $3}')
next_release=$(perl -pe 's/(\d+)$/($1+1)/e' <<< "${last_release}")
gh release create --generate-notes --notes-start-tag "${last_release}" "${next_release}"

sfkit_dir="sfkit/"
platforms=$(
    docker buildx imagetools inspect "${IMAGE}" \
        --format '{{range .Manifest.Manifests}}{{with .Platform}}{{if (ne .OS "unknown")}}  {{.OS}}/{{.Architecture}}{{if .Variant}}/{{.Variant}}{{end}}{{end}}{{end}}{{end}}'
)
for p in ${platforms} ; do
    (
        tmp_dir=$(mktemp -d)
        pushd "${tmp_dir}"

        # extract sfkit dir from the platform image
        crane export "${IMAGE}" - --platform "$p" | tar -xf - "${sfkit_dir}"

        # compress that dir into archive asset
        asset="${p//\//_}.tar.gz"
        tar -czf "${asset}" "${sfkit_dir}"

        # Currently, we have to retry upload of each asset,
        # due to intermittent issues with file uploads:
        # https://github.com/cli/cli/issues/7750
        n=1
        max=3
        while true ; do
            if gh release upload "${next_release}" "${asset}" ; then
                break
            else
                if [[ $n -lt $max ]]; then
                    sleep $n
                    ((n++))
                    echo "Retrying upload for ${asset} (attempt $n/$max):"
                else
                    echo "Upload for ${asset} failed after $n attempts."
                    exit 1
                fi
            fi
        done

        popd
        rm -rf "${tmp_dir}"
    ) &
done
wait -n
