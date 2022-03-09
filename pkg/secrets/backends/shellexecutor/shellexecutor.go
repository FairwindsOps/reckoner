package shellexecutor

import "os"

type ShellExecutor struct {
	Script     string
	Shell      string
	Executable string
	Path       string
}

func (s ShellExecutor) Get(key string) (string, error) {
	return "", nil
}

func (s ShellExecutor) SetEnv(key, value string) error {
	return os.Setenv(key, value)
}
