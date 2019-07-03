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

# Change to the script dir for help finding yamls
cd "$(dirname "${0}")"

# Mark the whole suite as failed
function mark_failed() {
    local err="Failed test: ${1} due to ${2}"
    echo "${err}"
    E2E_FAILED_TESTS=true
    E2E_FAILED_MESSAGES+=("${err}\n")
}

# Helper to clean out all the stuff between tests
function clean_helm() {
    if [ -z "${E2E_LEAVE_INSTALLED_CHARTS}" ]; then
        # Get all installed things in helm and delete/purge them
        helm list --output json | jq '.Releases[].Name' | xargs -I {} helm delete --purge {}
    fi
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
    if helm list --output json | jq -e ".Releases[]|select(.Name == \"${release_name}\")|.Namespace == \"${namespace}\" and .Status == \"DEPLOYED\""; then
        return 0
    else
        return 1
    fi
}

function helm_release_has_key_value() {
    local release_name="${1}"
    local key="${2}"
    local value="${3}"

    if helm get values "${release_name}" --output json | jq -e ".[\"${key}\"] == \"${value}\""; then
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

    if ! helm_has_release_name_in_namespace "nginx-ingress" "infra"; then
        mark_failed "${FUNCNAME[0]}" "did not find release in helm"
    fi

    if ! helm_release_has_key_value "nginx-ingress" "non-used" "testing"; then
        mark_failed "${FUNCNAME[0]}" "variable didn't end up in chart values"
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

    if ! helm_has_release_name_in_namespace "go-harbor" "test"; then
        mark_failed "${FUNCNAME[0]}" "Expected git chart release to be installed"
    fi

    #special cleanup task due to chart artifacts
    helm delete --purge go-harbor
    kubectl delete pvc -n test --all
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
    local first_chart_timestamp="$(helm ls -a --output json | jq '.Releases[] |select(.Name == "first-chart") | .Updated' -r | sed -E 's/ +/ /g' | xargs -I {} date -d {} +%s)"
    local second_chart_timestamp="$(helm ls -a --output json | jq '.Releases[] |select(.Name == "second-chart") | .Updated' -r | sed -E 's/ +/ /g' | xargs -I {} date -d {} +%s)"
    if [[ $(($first_chart_timestamp-$second_chart_timestamp)) -ge 0 ]]; then
        mark_failed "${FUNCNAME[0]}" "Expected timestamp for 'first-chart' to be before 'second-timestamp': Expected 'first-chart' to be installed first..."
    fi
}

# list all functions loaded, grab the function name (last element awk) and grep for any starting with e2e_test...
e2e_tests="$(declare -F | awk '{print $NF}' | grep ^e2e_test)"


if [[ "${1}" =~ ^e2e_test_ ]]; then
    # Run a specific test
    ${1}
    clean_helm
else
    for e2e_test in ${e2e_tests}; do
        ${e2e_test}

        # Clean up Helm between tests
        clean_helm
    done
fi

# Exit with a bad code if we failed any tests
if $E2E_FAILED_TESTS; then
    echo -e "* * *\nFound Failed Tests"
    echo -e "${E2E_FAILED_MESSAGES[@]}"
    exit 1
else
    echo "ALL TESTS PASSED!!"
    exit 0
fi
