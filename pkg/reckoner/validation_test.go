// Copyright 2020 Fairwinds
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License

package reckoner

import (
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestValidateArgs(t *testing.T) {
	var runAll bool
	var onlyRun []string
	var args []string

	courseFile, err := ValidateArgs(runAll, onlyRun, args)
	assert.Error(t, err)
	assert.Empty(t, courseFile)

	args = []string{"course.yaml"}
	courseFile, err = ValidateArgs(runAll, onlyRun, args)
	assert.Error(t, err)
	assert.Empty(t, courseFile)

	_, err = os.Create("course.yaml")
	assert.NoError(t, err)

	courseFile, err = ValidateArgs(runAll, onlyRun, args)
	assert.NoError(t, err)
	assert.Equal(t, "course.yaml", courseFile)

	runAll = true
	onlyRun = []string{"rbac-manager"}
	courseFile, err = ValidateArgs(runAll, onlyRun, args)
	assert.Error(t, err, "Only one of runAll or onlyRun can be set")
	assert.Empty(t, courseFile)

	runAll = false
	onlyRun = []string{"rbac-manager"}
	courseFile, err = ValidateArgs(runAll, onlyRun, args)
	assert.NoError(t, err, "Only one of runAll or onlyRun can be set")
	assert.Equal(t, "course.yaml", courseFile)

	runAll = true
	onlyRun = []string{}
	courseFile, err = ValidateArgs(runAll, onlyRun, args)
	assert.NoError(t, err, "Only one of runAll or onlyRun can be set")
	assert.Equal(t, "course.yaml", courseFile)

	err = os.Remove("course.yaml")
	assert.NoError(t, err)
}
