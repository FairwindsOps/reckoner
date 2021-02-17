package reckoner

import (
	"fmt"
	"os"
)

// ValidateArgs validates that the correct arguments were passed and returns the name of the course file
func ValidateArgs(runAll bool, onlyRun, args []string) (string, error) {
	if runAll && len(onlyRun) != 0 {
		return "", fmt.Errorf("you must either use run-all or only")
	}

	if !runAll && len(onlyRun) == 0 {
		return "", fmt.Errorf("you must use at least one of run-all or only")
	}

	if len(args) != 1 {
		return "", fmt.Errorf("you must pass a single course file argument")
	}

	_, err := os.Stat(args[0])
	if os.IsNotExist(err) {
		return "", fmt.Errorf("specified course file %s does not exist", args[0])
	}
	return args[0], err
}
