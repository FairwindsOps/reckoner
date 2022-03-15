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
