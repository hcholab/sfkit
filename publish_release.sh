#!/usr/bin/env bash
#
# Extracts platform-specific TAR archives
# containing static executables from the OCI image tar,
# and publishes them in a GitHub release.
#
# For more details, see
# https://stackoverflow.com/a/72952846/2962507

set -euxo pipefail

PLATFORMS=$1
OCI_TAR=$2

sfkit_dir="sfkit/"
dist_dir="$(pwd)/dist"
rm -rf "${dist_dir}"

oci_dir="ocidir://${dist_dir}/oci"
regctl image import "${oci_dir}" "${OCI_TAR}"

archive_base="${dist_dir}/sfkit_"

for p in ${PLATFORMS//,/ } ; do
    (
        pushd "$(mktemp -d)"
        digest=$(regctl image digest -p "$p" "${oci_dir}")

        regctl image export "${oci_dir}@${digest}" \
        | crane export - - --platform "$p" \
        | tar -xf - "${sfkit_dir}"

        tar -czf "${archive_base}${p//\//_}.tar.gz" "${sfkit_dir}"
        rm -rf "${sfkit_dir}"
        popd
    ) &
done
wait

last_release=$(gh release list -L 1 | awk '{print $3}')
next_release=$(perl -pe 's/(\d+)$/($1+1)/e' <<< "${last_release}")

gh release create --generate-notes \
    --notes-start-tag "${last_release}" "${next_release}" "${archive_base}"*

rm -rf "${dist_dir}"
