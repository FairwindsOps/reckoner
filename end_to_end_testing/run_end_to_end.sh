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
HELM_VERSION="${HELM_VERSION:-2}"

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
        if [ "${HELM_VERSION}" -eq "3" ]; then
            for namespace in  $(kubectl get ns  -o json | jq -r '.items[].metadata.name'); do
                helm list --namespace "${namespace}" --output json | jq '.[].name' | xargs -I {} helm delete --namespace "${namespace}" {}
            done
        else
            helm list  --output json | jq '.Releases[].Name' | xargs -I {} helm delete --purge {}
        fi
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

    if [ "${HELM_VERSION}" -eq "3" ]; then
        # If json list is empty then the release cannot exist, return false
        if [ "$(helm list --namespace ${namespace} --output json)" == "" ]; then
            return 1
        fi

        # if the release exists and is in the namespace and is DEPLOYED, then return true, otherwise false
        if helm list --namespace "${namespace}" --output json | jq -e ".[]|select(.name == \"${release_name}\")|.namespace == \"${namespace}\" and .status == \"deployed\"" &>/dev/null; then
            return 0
        else
            return 1
        fi
    else
        # If json list is empty then the release cannot exist, return false
        if [ "$(helm list --output json)" == "" ]; then
            return 1
        fi

        # if the release exists and is in the namespace and is DEPLOYED, then return true, otherwise false
        if helm list --output json | jq -e ".Releases[]|select(.Name == \"${release_name}\")|.Namespace == \"${namespace}\" and .Status == \"DEPLOYED\"" &>/dev/null; then
            return 0
        else
            return 1
        fi
    fi
}


function namespace_has_annotation_with_value() {
    local annotation_value="${3}"
    local annotation_name="${2}"
    local namespace="${1}"

    annotations=($(kubectl get namespace ${namespace}  -o json | jq -r '.metadata.annotations | keys[]'))
    values=($(kubectl get namespace ${namespace}  -o json | jq -r '.metadata.annotations[]'))

    for i in "${!annotations[@]}"; do
        if [ "${annotations[i]}" == "$annotation_name" ]; then
            if [ "${values[i]}" == "$annotation_value" ]; then
                return 0
            fi
        fi
    done
    return 1
}


function namespace_has_label_with_value() {
    local label_value="${3}"
    local label_name="${2}"
    local namespace="${1}"

    labels=($(kubectl get namespace ${namespace}  -o json | jq -r '.metadata.labels | keys[]'))
    values=($(kubectl get namespace ${namespace}  -o json | jq -r '.metadata.labels[]'))

    for i in "${!labels[@]}"; do
        if [ "${labels[i]}" == "$label_name" ]; then
            if [ "${values[i]}" == "$label_value" ]; then
                return 0
            fi
        fi
    done
    return 1
}

# check for deployed release in namespace
function release_namespace(){
    helm list --all-namespaces --output json | jq -r ".[]|select(.name == \"${1}\")|.namespace" | head -n 1
}

function helm_get_values(){

    if [ "${HELM_VERSION}" -eq "3" ]; then
        namespace=$(release_namespace ${1})
        helm get values --output=json --namespace "${namespace}" "${1}"
    else
        helm get values --output=json "${1}"
    fi
}

function helm_release_has_key_value() {
    local release_name="${1}"
    local key="${2}"
    local value="${3}"

    if helm_get_values "${release_name}"  | jq -e ".[\"${key}\"] == \"${value}\"" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

function helm_release_values_has_key() {
    local release_name="${1}"
    local key="${2}"

    if helm_get_values "${release_name}" --output json | jq -e ". | has(\"${key}\")" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

function helm_release_key_value_is_type() {
    local release_name="${1}"
    local key="${2}"
    local type="${3}"

    if helm_get_values "${release_name}" --output json | jq -e ".[\"${key}\"] | type == \"${type}\"" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

function e2e_test_namespace_creation_flag_on_chart_install() {
    if [ "${HELM_VERSION}" -eq "3" ]; then
        if reckoner plot --no-create-namespace test_create_namespace.yml --run-all; then
            mark_failed "${FUNCNAME[0]}" "With --no-create-namespace set, this should have failed"
        fi

        if helm_has_release_name_in_namespace "namespace-test" "farglebargle"; then
            mark_failed "${FUNCNAME[0]}" "Found namespace_test in farglebargle namespace after install and should not have"
        fi

        if ! reckoner plot test_create_namespace.yml --run-all; then
            mark_failed "${FUNCNAME[0]}" "Without --no-create-namespace set, this should not have failed"
        fi

        if ! helm_has_release_name_in_namespace "namespace-test" "farglebargle"; then
            mark_failed "${FUNCNAME[0]}" "Did not find namespace_test in farglebargle namespace after install."
        fi
    fi


}

function e2e_test_basic_chart_install() {
    if ! reckoner plot test_basic.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Plot had a bad exit code"
    fi

    if ! helm_has_release_name_in_namespace "first-chart" "infra"; then
        mark_failed "${FUNCNAME[0]}" "Did not find nginx-ingress in infra namespace after install."
    fi
}

function e2e_test_env_var() {
    if ! myvar=testing reckoner plot test_env_var.yml --run-all; then
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
    if reckoner plot test_env_var.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Should fail to plot course without env var."
    fi
}

function e2e_test_good_hooks() {
    if ! reckoner plot test_good_hooks.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Plot had bad exit code"
    fi

    # TODO: Verify the hooks passed specifically (this just tests the exit code)
}

function e2e_test_exit_on_post_install_hook() {
    # we expect this to fail exit code != 0
    if reckoner plot test_exit_on_post_install_hook.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected plot to have a bad exit code"
    fi

    if ! helm_has_release_name_in_namespace "nginx-ingress" "infra"; then
        mark_failed "${FUNCNAME[0]}" "Expected to have chart installed, despite bad post-install hook"
    fi
}

function e2e_test_exit_on_pre_install_hook() {
    # we expect this to fail exit code != 0
    if reckoner plot test_exit_on_pre_install_hook.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected plot to have a bad exit code"
    fi

    # we don't expect nginx-ingress to be installed
    if helm_has_release_name_in_namespace "nginx-ingress" "infra"; then
        mark_failed "${FUNCNAME[0]}" "Expected chart to NOT be installed due to pre-install hook"
    fi
}

function e2e_test_failed_chart() {
    # we expect this command to have a bad exit code
    if reckoner plot test_failed_chart.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected plot to fail with bad exit code"
    fi

    if helm_has_release_name_in_namespace "bad-chart" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected chart to not be installed due to missing required params"
    fi
}

function e2e_test_multi_chart() {
    if ! reckoner plot test_multi_chart.yml --run-all; then
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
    if ! reckoner plot test_git_chart.yml --run-all; then
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
    if [ "${HELM_VERSION}" -eq "3" ]; then
        helm delete --namespace test go-harbor
    else
        helm delete --purge go-harbor
    fi

    kubectl delete pvc --all-namespaces --all
}

function e2e_test_stop_after_first_failure() {
    # we expect a non-zero exit code here
    if reckoner plot test_stop_after_first_failure.yml --run-all; then
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
    if reckoner plot --continue-on-error test_continue_after_first_failure.yml --run-all; then
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

    local second_chart_timestamp


    if [ "${HELM_VERSION}" -eq "3" ]; then
        first_chart_timestamp="$(helm ls --namespace test -a --output json | jq '.[] |select(.name == "first-chart") | .updated' -r | awk -F"." '{ print $1 }' | tr -d \\n | xargs -I {} date -d {} +%s)"
        second_chart_timestamp="$(helm ls --namespace test -a --output json | jq '.[] |select(.name == "second-chart") | .updated' -r | awk -F"." '{ print $1 }' | tr -d \\n | xargs -I {} date -d {} +%s)"
    else
        first_chart_timestamp="$(helm ls -a --output json | jq '.Releases[] |select(.Name == "first-chart") | .Updated' -r | sed -E 's/ +/ /g' | xargs -I {} date -d {} +%s)"
        second_chart_timestamp="$(helm ls -a --output json | jq '.Releases[] |select(.Name == "second-chart") | .Updated' -r | sed -E 's/ +/ /g' | xargs -I {} date -d {} +%s)"
    fi

    if [[ $((first_chart_timestamp-second_chart_timestamp)) -ge 0 ]]; then
        mark_failed "${FUNCNAME[0]}" "Expected timestamp for 'first-chart' to be before 'second-timestamp': Expected 'first-chart' to be installed first..."
    fi
}

function e2e_test_strong_typing() {
    if ! yes_var=yes true_var=true false_var=false int_var=123 float_var=1.234 reckoner plot test_strong_typing.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected the course to be installable."
    fi

    local charts
    if [ "${HELM_VERSION}" -eq "3" ]; then
        charts="$(helm ls --namespace testing --output json | jq -e -r '.[].name')"
    else
        charts="$(helm ls --output json | jq -e -r '.Releases[].Name')"
    fi

    for _release_install in ${charts}; do
        # Check if the chart is installed
        if ! helm_has_release_name_in_namespace "${_release_install}" "testing"; then
            mark_failed "${FUNCNAME[0]}" "Expected release to be installed"
            continue
        fi

        # Check that all charts have these keys
        local values

        if [ "${HELM_VERSION}" -eq "3" ]; then
            values="$(helm get values --namespace testing "${_release_install}" --output json | jq -e -r 'keys|.[]')"
        else
            values="$(helm get values "${_release_install}" --output json | jq -e -r 'keys|.[]')"
        fi

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
                mark_failed "${FUNCNAME[0]}" "Expected chart (${_release_install}) value for key (${key}) to be (${_expected_type}). Got ($(helm get values --namespace test "${_release_install}" --output json | jq -cr ".[\"${key}\"]|type"))"
            fi
        done
    done
}

function e2e_test_bad_schema_repository() {
    if reckoner plot test_bad_schema_repository.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected to fail on schema validation failure."
    fi
}

function e2e_test_required_schema() {
    if reckoner plot test_required_schema.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected to fail on schema validation failure."
    fi
}

function e2e_test_files_in_folders() {
    if ! reckoner plot testing_in_folder/test_files_in_folders.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected to run without an error."
    fi

    if ! helm_release_has_key_value "chart-one" "new_key" "new_value"; then
        mark_failed "${FUNCNAME[0]}" "Expected file values yaml in a subfolder to work."
    fi
}

function e2e_test_default_namespace_management(){
    if ! reckoner plot test_default_namespace_annotation_and_labels.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected to run without an error."
    fi

    if ! namespace_has_annotation_with_value annotatednamespace reckoner rocks; then
        mark_failed "${FUNCNAME[0]}" "Expected annotation on namespace."
    fi

    if ! namespace_has_label_with_value annotatednamespace rocks reckoner; then
        mark_failed "${FUNCNAME[0]}" "Expected label on namespace."
    fi
}

function e2e_test_overwrite_namespace_management(){
    if ! reckoner plot test_overwrite_namespace_annotation_and_labels.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected to run without an error."
    fi

    if ! namespace_has_annotation_with_value annotatednamespace reckoner doesnotrock; then
        mark_failed "${FUNCNAME[0]}" "Expected annotation on namespace."
    fi

    if ! namespace_has_label_with_value annotatednamespace rocks reckonerstill; then
        mark_failed "${FUNCNAME[0]}" "Expected label on namespace."
    fi
}

function e2e_test_does_not_overwrite_namespace_management(){
    if ! reckoner plot test_overwrite_namespace_annotation_and_labels.yml --run-all; then
        mark_failed "${FUNCNAME[0]}" "Expected to run without an error."
    fi

    if ! namespace_has_annotation_with_value annotatednamespace reckoner doesnotrock; then
        mark_failed "${FUNCNAME[0]}" "Expected annotation on namespace."
    fi

    if ! namespace_has_label_with_value annotatednamespace rocks reckonerstill; then
        mark_failed "${FUNCNAME[0]}" "Expected label on namespace."
    fi
}

function e2e_test_template() {
    if [ "${HELM_VERSION}" -eq "3" ]; then
        if ! reckoner template test_basic.yml --run-all; then
            mark_failed "${FUNCNAME[0]}" "Expected to get templates of one release without an error."
        fi
    fi
}

function e2e_test_get_manifests() {
    if [ "${HELM_VERSION}" -eq "3" ]; then
        reckoner plot test_basic.yml --run-all
        if ! reckoner get-manifests test_basic.yml -o first-chart; then
            mark_failed "${FUNCNAME[0]}" "Expected to get manifests of one release without an error."
        fi
    fi
}

function e2e_test_get_manifests_non_existent() {
    if [ "${HELM_VERSION}" -eq "3" ]; then
        reckoner plot test_basic.yml --run-all
        if reckoner get-manifests test_basic.yml -o non-existent; then
            mark_failed "${FUNCNAME[0]}" "Expected to fail getting non-existent release"
        fi
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
