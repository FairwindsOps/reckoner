
from kubernetes import client, config


class NamespaceManagerMock(object):

    def __init__(self, namespace_name='', namespace_management={}) -> None:
        """ Manages a namespace for the chart
        Accepts:
        - namespace: Which may be a string or a dictionary
        """
        self._namespace_name = namespace_name
        self._metadata = namespace_management.get('metadata', {})
        self._overwrite = namespace_management.get(
            'settings',
            {}
        ).get(
            'overwrite',
            False
        )
        self.__load_config()

    @property
    def namespace_name(self) -> str:
        """ Name of the namespace we are managing """
        return self._namespace_name

    @property
    def namespace(self) -> str:
        """ Namespace object we are managing 
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Namespace.md"""
        return self._namespace

    @property
    def metadata(self) -> dict:
        """ List of metadata settings parsed from the
        from the chart and course """
        return self._metadata

    @property
    def overwrite(self) -> bool:
        """ List of metadata settings parsed from the
        from the chart and course """
        return self._overwrite

    def __load_config(self):
        """ Protected method do load kubernetes config"""
        pass

    def create_and_manage(self):
        """ Create namespace and patch metadata """
        self._namespace = self.create()
        self.patch_metadata()

    def patch_metadata(self):
        """ Patch namepace with metadata respecting overwrite setting.
        Returns True on success
        Raises error on failure
        """
        pass

    def create(self):
        """ Create a namespace in the configured kubernetes cluster if it does not already exist

        Arguments:
        None

        Returns Namespace
        Raises error in case of failure

        """
        return client.V1Namespace(
            metadata=client.V1ObjectMeta(name=self.namespace_name)
        )

    @property
    def cluster_namespaces(self) -> list:
        """ Lists namespaces in the configured kubernetes cluster.
        No arguments
        Returns list of namespace objects
        """
        return []
