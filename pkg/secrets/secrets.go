// Copyright 2022 Fairwinds
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

package secrets

import "os"

type Getter interface {
	Get(key string) (string, error)
}

type Backend struct {
	getter Getter
}

// NewSecretBackend creates a new SecretBackend based on a concrete secrets.Getter implementation.
func NewSecretBackend(getter Getter) *Backend {
	return &Backend{getter: getter}
}

// SetEnv populates the current ENV with the given secret key by fetching it from the SecretBackend and calling os.Setenv.
func (b Backend) SetEnv(key string) error {
	value, err := b.get(key)
	if err != nil {
		return err
	}
	return os.Setenv(key, value)
}

// get fetches a secret from the implemented SecretBackend.
func (b Backend) get(key string) (string, error) {
	return b.getter.Get(key)
}
