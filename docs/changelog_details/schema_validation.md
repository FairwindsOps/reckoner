# Schema Validation
This document refers to the changes in v2.1.0 that introduce schema validation on the course.yml.

## What is Changing
1. The entire course is now being validated and checking if your course is valid before running any helm commands
2. Duplicate keys in your course yaml are no longer accepted: (example below)

## What is the valid schema
You can find the schema, defined as `json-schema`, in [this file](https://github.com/FairwindsOps/reckoner/blob/master/reckoner/assets/course.schema.json). To learn more about `json-schema`, visit the [JSON Schema Reference Site](https://json-schema.org/understanding-json-schema/reference/index.html).

## Common errors
### Duplicate keys
Below is an example of a duplicate key error. We've defined the `resources.requests` key twice. This would normally lead to unexpected behavior of merging the two keys together (inconsistent between yaml libraries) and you could find yourself in a scenario where you're not setting the `memory: 100Mi` as you might expect. The new behavior of reckoner will not run until you clean up the duplicate definitions.

```yaml
# course.yml
...
charts:
    nginx-ingress:
        namespace: default
        values:
            resources:
                requests:
                    cpu: 100m
                    memory: 100Mi
                limits:
                    cpu: 150m
                    memory: 150Mi
                requests:
                    cpu: 100m
...
```
