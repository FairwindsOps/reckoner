#!/bin/bash

# Run all end to end tests here as functions
# The concept is to run all the tests and if any fail, mark it as failed.
# We *always* want to run *all* tests though, to assure we know which ones
# have failed, so we can fix multile at a time vs waiting for CI to catch
# one issue at a time.

# NOTE: You must label your test as "e2e_test...() {}"

set -e
set -o pipefail
set -o errtrace

E2E_FAILED_TESTS=false
E2E_FAILED_MESSAGES=()
E2E_SKIPPED_MESSAGES=()

function print_status_end_exit() {
    if [ "${#E2E_SKIPPED_MESSAGES[@]}" -gt 0 ]; then echo -e "* * *\nSkipped Tests:"; fi
    for skipped_test in "${E2E_SKIPPED_MESSAGES[@]}"; do
        echo -en "- ${skipped_test}"
    done

    # Exit with a bad code if we failed any tests
    if $E2E_FAILED_TESTS; then
        echo -e "* * *\nFound Failed Tests"
        for error_message in "${E2E_FAILED_MESSAGES[@]}"; do
            echo -en "- ${error_message}"
        done
        exit 1
    else
        echo "ALL TESTS PASSED!!"
        exit 0
    fi
}

trap 'echo Failed unexpectedly on line ${BASH_LINENO} running ${FUNCNAME[0]}: ${BASH_COMMAND}; clean_helm; exit 1' ERR

# Change to the script dir for help finding yamls
cd "$(dirname "${0}")"

# Helper to clean out all the stuff between tests
function clean_helm() {
    if [ -z "${E2E_LEAVE_INSTALLED_CHARTS}" ]; then
        # Get all installed things in helm and delete/purge them
        helm list --output json | jq '.Releases[].Name' | xargs -I {} helm delete --purge {}
    fi
}

# Mark the whole suite as failed
function mark_failed() {
    local err
    err="Failed test: ${1} due to ${2}"
    echo "${err}"
    E2E_FAILED_TESTS=true
    E2E_FAILED_MESSAGES+=("${err}\n")
}

function add_skipped_message() {
    local msg="${1}"
    E2E_SKIPPED_MESSAGES+=("${msg}\n")
}

# check for deployed release in namespace
function helm_has_release_name_in_namespace() {
    local release_name="${1}"
    local namespace="${2}"

    # If json list is empty then the release cannot exit, return false
    if [ "$(helm list --output json)" == "" ]; then
        return 1
    fi

    # if the release exists and is in the namespace and is DEPLOYED, then return true, otherwise false
    if helm list --output json | jq -e ".Releases[]|select(.Name == \"${release_name}\")|.Namespace == \"${namespace}\" and .Status == \"DEPLOYED\"" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

function helm_release_has_key_value() {
    local release_name="${1}"
    local key="${2}"
    local value="${3}"

    if helm get values "${release_name}" --output json | jq -e ".[\"${key}\"] == \"${value}\"" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

function helm_release_values_has_key() {
    local release_name="${1}"
    local key="${2}"

    if helm get values "${release_name}" --output json | jq -e ". | has(\"${key}\")" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

function helm_release_key_value_is_type() {
    local release_name="${1}"
    local key="${2}"
    local type="${3}"

    if helm get values "${release_name}" --output json | jq -e ".[\"${key}\"] | type == \"${type}\"" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

function e2e_test_basic_chart_install() {
    if ! reckoner plot test_basic.yml; then
        mark_failed "${FUNCNAME[0]}" "Plot had a bad exit code"
    fi

    if ! helm_has_release_name_in_namespace "first-chart" "infra"; then
        mark_failed "${FUNCNAME[0]}" "Did not find nginx-ingress in infra namespace after install."
    fi
}

function e2e_test_env_var() {
    if ! myvar=testing reckoner plot test_env_var.yml; then
        mark_failed "${FUNCNAME[0]}" "Could not install course"
    fi

    if ! helm_release_has_key_value "check-values" "non-used" "testing"; then
        mark_failed "${FUNCNAME[0]}" "variable didn't end up using values"
    fi

    if ! helm_release_has_key_value "check-set-values" "non-used" "testing"; then
        mark_failed "${FUNCNAME[0]}" "variable didn't end up using set values"
    fi

    if ! helm_release_has_key_value "check-values-strings" "non-used" "testing"; then
        mark_failed "${FUNCNAME[0]}" "variable didn't end up using values-strings"
    fi
}

function e2e_test_env_var_exit_code() {
    if reckoner plot test_env_var.yml; then
        mark_failed "${FUNCNAME[0]}" "Should fail to plot course without env var."
    fi
}

function e2e_test_good_hooks() {
    if ! reckoner plot test_good_hooks.yml; then
        mark_failed "${FUNCNAME[0]}" "Plot had bad exit code"
    fi

    # TODO: Verify the hooks passed specifically (this just tests the exit code)
}

function e2e_test_exit_on_post_install_hook() {
    # we expect this to fail exit code != 0
    if reckoner plot test_exit_on_post_install_hook.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected plot to have a bad exit code"
    fi

    if ! helm_has_release_name_in_namespace "nginx-ingress" "infra"; then
        mark_failed "${FUNCNAME[0]}" "Expected to have chart installed, despite bad post-install hook"
    fi
}

function e2e_test_exit_on_pre_install_hook() {
    # we expect this to fail exit code != 0
    if reckoner plot test_exit_on_pre_install_hook.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected plot to have a bad exit code"
    fi

    # we don't expect nginx-ingress to be installed
    if helm_has_release_name_in_namespace "nginx-ingress" "infra"; then
        mark_failed "${FUNCNAME[0]}" "Expected chart to NOT be installed due to pre-install hook"
    fi
}

function e2e_test_failed_chart() {
    # we expect this command to have a bad exit code
    if reckoner plot test_failed_chart.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected plot to fail with bad exit code"
    fi

    if helm_has_release_name_in_namespace "bad-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected chart to not be installed due to missing required params"
    fi
}

function e2e_test_multi_chart() {
    if ! reckoner plot test_multi_chart.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected plot to succeed"
    fi

    if ! helm_has_release_name_in_namespace "first-chart" "infra"; then
        mark_failed "${FUNCNAME[0]}" "Expected first-chart to be installed in infra namespace"
    fi

    if ! helm_has_release_name_in_namespace "second-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected second-chart to be installed in default namespace for course (test)"
    fi
}

function e2e_test_install_only_one_chart() {
    if ! reckoner plot --only first-chart test_multi_chart.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected plot command with --only to pass"
    fi

    if ! helm_has_release_name_in_namespace "first-chart" "infra"; then
        mark_failed "${FUNCNAME[0]}" "Expected plot to install first-chart"
    fi
    
    # we do not expect second-chart due to --only
    if helm_has_release_name_in_namespace "second-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected second-chart to be ignored due to --only flag"
    fi
}

function e2e_test_git_chart() {
    if ! reckoner plot test_git_chart.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected chart plot to succeed"
    fi

    if ! helm_has_release_name_in_namespace "polaris-release" "polaris"; then
        mark_failed "${FUNCNAME[0]}" "Expected git chart release to be installed"
    fi

    if ! helm_has_release_name_in_namespace "polaris" "another-polaris"; then
        mark_failed "${FUNCNAME[0]}" "Expected git chart release to be installed"
    fi

    if ! helm_has_release_name_in_namespace "go-harbor" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected git chart release to be installed"
    fi

    # Special Clean up of GoHarbor
    helm delete --purge go-harbor
    kubectl delete pvc --all-namespaces --all
}

function e2e_test_stop_after_first_failure() {
    # we expect a non-zero exit code here
    if reckoner plot test_stop_after_first_failure.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected reckoner to exit with a bad exit code."
    fi

    if ! helm_has_release_name_in_namespace "good-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected 'good-chart' to be installed before 'bad-chart' failure"
    fi

    if helm_has_release_name_in_namespace "bad-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Did not expect 'bad-chart' to install, expected to fail"
    fi

    if helm_has_release_name_in_namespace "expected-skipped-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected this chart to skip being installed due to 'bad-chart' failing to install"
    fi
}

function e2e_test_continue_after_first_failure() {
    # we expect a non-zero exit code here
    if reckoner plot --continue-on-error test_continue_after_first_failure.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected reckoner to exit with a bad exit code."
    fi

    if ! helm_has_release_name_in_namespace "good-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected 'good-chart' to be installed before 'bad-chart' failure"
    fi

    if helm_has_release_name_in_namespace "bad-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Did not expect 'bad-chart' to install, expected to fail"
    fi

    if ! helm_has_release_name_in_namespace "expected-skipped-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected this chart to be installed even if 'bad-chart' fail to install (--continue-on-error set)"
    fi
}

function e2e_test_strong_ordering() {
    # NOTE We expect the charts to be installed in the order defined on the course.yml ALWAYS
    if ! reckoner plot test_strong_ordering.yml --only second-chart --only first-chart; then
        mark_failed "${FUNCNAME[0]}" "Expected reckoner to exit with a bad exit code."
    fi

    if ! helm_has_release_name_in_namespace "first-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected 'first-chart' to be installed"
    fi

    if ! helm_has_release_name_in_namespace "second-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected 'second-chart' to be installed"
    fi

    # Custom check which subtracts the two modified timestamps
    # This will fail if they are modified at the same second...
    local first_chart_timestamp
    first_chart_timestamp="$(helm ls -a --output json | jq '.Releases[] |select(.Name == "first-chart") | .Updated' -r | sed -E 's/ +/ /g' | xargs -I {} date -d {} +%s)"
    local second_chart_timestamp
    second_chart_timestamp="$(helm ls -a --output json | jq '.Releases[] |select(.Name == "second-chart") | .Updated' -r | sed -E 's/ +/ /g' | xargs -I {} date -d {} +%s)"
    if [[ $((first_chart_timestamp-second_chart_timestamp)) -ge 0 ]]; then
        mark_failed "${FUNCNAME[0]}" "Expected timestamp for 'first-chart' to be before 'second-timestamp': Expected 'first-chart' to be installed first..."
    fi
}

function e2e_test_strong_typing() {
    if ! yes_var=yes true_var=true false_var=false int_var=123 float_var=1.234 reckoner plot test_strong_typing.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected the course to be installable."
    fi

    local charts
    charts="$(helm ls --output json | jq -e -r '.Releases[].Name')"
    for _release_install in ${charts}; do
        # Check if the chart is installed
        if ! helm_has_release_name_in_namespace "${_release_install}" "testing"; then
            mark_failed "${FUNCNAME[0]}" "Expected release to be installed"
            continue
        fi

        # Check that all charts have these keys
        local values
        values="$(helm get values "${_release_install}" --output json | jq -e -r 'keys|.[]')"
        for key in ${values}; do
            # Check if the chart has this key
            if ! helm_release_values_has_key "${_release_install}" "${key}"; then
                mark_failed "${FUNCNAME[0]}" "Expected release (${_release_install}) to have key: (${key})."
                continue
            fi

            local _expected_type
            # Check type of key found in json
            case "${key}" in
                expect-float*)
                    _expected_type="number"
                    ;;
                expect-integer*)
                    _expected_type="number"
                    ;;
                expect-string*)
                    _expected_type="string"
                    ;;
                expect-bool*)
                    _expected_type="boolean"
                    ;;
                expect-null*)
                    _expected_type="null"
                    ;;
                *)
                    mark_failed "${FUNCNAME[0]}" "Did not find how to convert expected keys to types for jq. Key(${key})"
                    continue
                    ;;
            esac

            if ! helm_release_key_value_is_type "${_release_install}" "${key}" "${_expected_type}"; then
                mark_failed "${FUNCNAME[0]}" "Expected chart (${_release_install}) value for key (${key}) to be (${_expected_type}). Got ($(helm get values "${_release_install}" --output json | jq -cr ".[\"${key}\"]|type"))"
            fi
        done
    done
}

function e2e_test_bad_schema_repository() {
    if reckoner plot test_bad_schema_repository.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected to fail on schema validation failure."
    fi
}

function e2e_test_required_schema() {
    if reckoner plot test_required_schema.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected to fail on schema validation failure."
    fi
}

function e2e_test_files_in_folders() {
    if ! reckoner plot testing_in_folder/test_files_in_folders.yml; then
        mark_failed "${FUNCNAME[0]}" "Expected to run without an error."
    fi

    if ! helm_release_has_key_value "chart-one" "new_key" "new_value"; then
        mark_failed "${FUNCNAME[0]}" "Expected file values yaml in a subfolder to work."
    fi
}

function run_test() {
    local test_name
    test_name="${1}"
    echo -e "\n\n* * * * * * * *"
    echo "Running ${test_name}"
    ${test_name}
    clean_helm
}

# list all functions loaded, grab the function name (last element awk) and grep for any starting with e2e_test...
e2e_tests="$(declare -F | awk '{print $NF}' | grep ^e2e_test)"


if [[ "${1}" =~ ^e2e_test_ ]]; then
    # Run a specific test
    run_test "${1}"
else
    for e2e_test in ${e2e_tests}; do
        run_test "${e2e_test}"
    done
fi

print_status_end_exit
