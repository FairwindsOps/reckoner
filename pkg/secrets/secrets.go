package secrets

import "os"

type Getter interface {
	Get(key string) (string, error)
}

type SecretBackend struct {
	getter Getter
}

// NewSecretBackend creates a new SecretBackend based on a concrete secrets.Getter implementation.
func NewSecretBackend(getter Getter) *SecretBackend {
	return &SecretBackend{getter: getter}
}

// Get fetches a secret from the implemented SecretBackend.
func (s SecretBackend) Get(key string) (string, error) {
	return s.getter.Get(key)
}

// SetEnv populates the current ENV with the given secret key by fetching it from the SecretBackend and calling os.Setenv.
func (s SecretBackend) SetEnv(key string) error {
	value, err := s.Get(key)
	if err != nil {
		return err
	}
	return os.Setenv(key, value)
}
