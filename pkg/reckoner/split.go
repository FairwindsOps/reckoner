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
	"strings"

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
		var b bytes.Buffer    // used for encoding & return

		err = decoder.Decode(&value) // attempt to decode a page in the document
		if err == io.EOF {           // we ran out of pages/objects/bytes
			break // stop trying to process anything
		}
		// we might have bytes, but we still need to check if we could decode successfully
		if err != nil { // check for errors
			return nil, err // bubble up
		}

		yamlEncoder := yaml.NewEncoder(&b) // create an encoder to handle custom configuration
		yamlEncoder.SetIndent(2)           // people expect two-space indents instead of the default four
		err = yamlEncoder.Encode(&value)   // encode proper YAML into slice of bytes
		if err != nil {                    // check for errors
			return nil, err // bubble up
		}

		// we believe we have a valid YAML object
		out = append(out, bytes.TrimSpace(b.Bytes())) // so append it to the list to be returned later
	}

	return out, nil // list of YAML objects, each a []byte
}

func writeYAML(in []byte, filename string) (err error) {
	file, err := os.Create(filename)
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

		if len(meta.Kind) < 1 || len(meta.Metadata.Name) < 1 { // skip empty objects; these are the required fields in k8sMetaBasic{}
			continue
		}

		// This section will build out the name of the file based on what was found inside of the object.
		// For example, an object with:
		//   kind: Deployment
		//   metadata:
		//     name: cool-app-api
		//     namespace: cool-app
		// will have the filename of: --output-dir/release_name/cool-app_deployment_cool-app-api.yaml
		// We also replace colons with underscores for windows compatibility since RBAC names may have colons
		filename := releasePath + "/"         // path for the release
		if len(meta.Metadata.Namespace) > 0 { // only add the namespace to the filename when it's found in the object
			filename = filename + strings.ToLower(meta.Metadata.Namespace) + "_" // lowercased for simplicity
		} // continue building the rest of the filename
		filename = filename + strings.ToLower(meta.Kind) + "_" + strings.ToLower(meta.Metadata.Name) + ".yaml" // lowercased for simplicity
		filename = strings.ReplaceAll(filename, ":", "_")                                                      // replace colons with underscores for windows compatibility; RBAC names may have colons

		err = writeYAML(object, filename) // write out
		if err != nil {
			return err
		}
	}

	return err
}
