package secrets

import "os"

type Getter interface {
	Get(key string) (string, error)
}

type SecretEngine struct {
	getter Getter
}

func NewSecretEngine(getter Getter) *SecretEngine {
	return &SecretEngine{getter: getter}
}

func (s SecretEngine) Get(key string) (string, error) {
	return s.getter.Get(key)
}

func (s SecretEngine) SetEnv(key, value string) error {
	return os.Setenv(key, value)
}
