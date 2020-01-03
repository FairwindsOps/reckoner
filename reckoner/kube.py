
import logging
import traceback

from kubernetes import client, config


def create_namespace(namespace):
    """ Create a namespace in the configured kubernetes cluster if it does not already exist

    Arguments:

    namespace: The namespace to create

    Returns True on success
    Raises error in case of failure

    """
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        response = v1.create_namespace(
            client.V1Namespace(
                metadata=client.V1ObjectMeta(name=namespace)
            )
        )
        return True
    except Exception as e:
        logging.error("Unable to create namespace in cluster! {}".format(e))
        logging.debug(traceback.format_exc())
        raise e


def list_namespace_names():
    """ Lists namespaces in the configured kubernetes cluster.
    No arguments
    Returns list
    """
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()
        return [namespace.metadata.name for namespace in namespaces.items]
    except Exception as e:
        logging.error("Unable to get namespaces in cluster! {}".format(e))
        logging.debug(traceback.format_exc())
        raise e
