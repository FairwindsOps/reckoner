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

package reckoner

import (
	"bytes"
	"errors"
	"io"
	"os"

	"gopkg.in/yaml.v3"
)

type k8sMetaBasic struct {
	Kind     string `yaml:"kind"`
	Metadata struct {
		Name      string `yaml:"name"`
		Namespace string `yaml:"namespace,omitempty"`
	} `yaml:"metadata"`
}

// splitYAML will take a slice of bytes, assumed to be a multi-page (1+) YAML document,
// and append each page/object it finds in the document to a slice which is
// returned at the end of processing. Each object is typed as a slice of bytes.
// Therefore, this function returns a slice of a slice of bytes.
// splitYAML was shamelessly ripped from https://go.dev/play/p/MZNwxdUzxPo, which was
// found via github issue https://github.com/go-yaml/yaml/pull/301#issuecomment-792871300
func splitYAML(in []byte) (out [][]byte, err error) {
	decoder := yaml.NewDecoder(bytes.NewReader(in)) // create a YAML decoder to run through our document

	for { // keep going until we run out of bytes to process (end-of-file/EOF)
		var value interface{} // something we can use to decode and marshal

		err = decoder.Decode(&value) // attempt to decode a page in the document
		if err == io.EOF {           // we ran out of pages/objects/bytes
			break // stop trying to process anything
		}
		// we might have bytes, but we still need to check if we could decode successfully
		if err != nil { // check for errors
			return nil, err // bubble up
		}

		valueBytes, err := yaml.Marshal(value) // marshal the slice of bytes into proper a YAML object
		if err != nil {                        // check for errors
			return nil, err // bubble up
		}

		// we believe we have a valid YAML object
		out = append(out, valueBytes) // so append it to the list to be returned later
	}

	return out, nil // list of YAML objects, each a []byte
}

func writeYAML(in []byte, filename string) (err error) {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}

	_, err = file.Write([]byte("---\n")) //  pagination, just in case a multi-document file is being written
	if err != nil {
		return err
	}

	_, err = file.Write(in)
	if err != nil {
		return err
	}

	return err
}

func (c *Client) WriteSplitYaml(in []byte, basePath string, releaseName string) (err error) {
	releasePath := basePath + "/" + releaseName

	objects, err := splitYAML(in) // get list of YAML documents
	if err != nil {               // check for errors
		return err // bubble up
	}

	// ensure "${--output-dir}/release_name" exists
	for _, dir := range []string{basePath, releasePath} {
		if _, err := os.Stat(dir); errors.Is(err, os.ErrNotExist) {
			err := os.Mkdir(dir, os.ModePerm)
			if err != nil {
				return err
			}
		}
	}

	for _, object := range objects { // loop through documents
		meta := k8sMetaBasic{}
		err = yaml.Unmarshal(object, &meta)
		if err != nil {
			return err
		}

		filename := releasePath + "/" + meta.Kind + "_" + meta.Metadata.Name + ".yml"

		err = writeYAML(object, filename) // write out
		if err != nil {
			return err
		}
	}

	return err
}
