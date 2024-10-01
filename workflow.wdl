version development

workflow sfkit {
  input {
    String study_id
    Directory? data
    Int num_cores = 16 # TODO: test with smaller CP0
    Int boot_disk_size_gb = 128
    String api_url = "https://sfkit.dsde-prod.broadinstitute.org/api"
    String docker = "us-central1-docker.pkg.dev/dsp-artifact-registry/sfkit/sfkit"
  }

  call cli {
    input:
      study_id = study_id,
      data = data,
      num_cores = num_cores,
      boot_disk_size_gb = boot_disk_size_gb,
      api_url = api_url,
      docker = docker,
  }
}

task cli {
  input {
    String study_id
    Directory? data
    Int num_cores
    Int boot_disk_size_gb
    String api_url
    String docker
  }

  command <<<
      set -xeu

      export SFKIT_API_URL="~{api_url}"
      cd /sfkit

      sfkit auth --study_id "~{study_id}"
      sfkit networking
      sfkit generate_keys

      if [ -n "~{data}" ]; then
        sfkit register_data --data_path "~{data}"
      fi

      sfkit run_protocol
  >>>

  runtime {
    docker: docker
    cpu: num_cores
    cpuPlatform: "Intel Ice Lake"
    memory: "~{num_cores * 8} GB"

    # TODO: allow specifying sfgwas cache directory inside /cromwell_root
    bootDiskSizeGb: boot_disk_size_gb
  }

  output {
    String out = read_string(stdout())
  }
}
