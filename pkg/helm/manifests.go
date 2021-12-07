package helm

// GetManifestString will run 'helm get manifest' on a given namespace and release and return the string output.
func (h Client) GetManifestString(namespace, release string) (string, error) {
	out, err := h.get("manifest", namespace, release)
	if err != nil {
		return "", err
	}
	return out, err
}
