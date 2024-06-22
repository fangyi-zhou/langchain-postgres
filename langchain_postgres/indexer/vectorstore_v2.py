import warnings
from abc import ABC, abstractmethod
from typing import (
    Any,
    AsyncIterable,
    Dict,
    Iterable,
    List,
    Optional,
    Union,
)

from langchain_core.documents import Document
from langchain_core.indexes.types import DeleteResponse, UpsertResponse
from langchain_core.runnables import run_in_executor
from langchain_core.structured_query import StructuredQuery

Vector = List[float]


class VectorIndex(ABC):
    """Interface to index documents and query them by vector representation.


    Example:
        .. code-block:: python

            from typing import Any, Iterator, List, Optional, Sequence, Tuple, Union, Iterable
            from uuid import uuid4

            from langchain_core.documents import Document
            from langchain_core.indexes import UpsertResponse, DeleteResponse, Index

            def uuid4_generator() -> Iterable[str]:
                while True:
                    yield str(uuid4())

            class DictIndex(Index):

                def __init__(self) -> None:
                    self.store = {}

                def upsert(
                    self,
                    documents: Iterable[Document],
                    *,
                    ids: Optional[Iterable[str]] = None,
                    **kwargs: Any,
                ) -> UpsertResponse:
                    ids = ids or uuid4_generator()
                    succeeded = []
                    for id_, doc in zip(ids, documents):
                        self.store[id_] = doc
                        succeeded.append(id_)
                    return UpsertResponse(succeeded=succeeded, failed=[])

                def delete_by_ids(self, ids: Iterable[str]) -> DeleteResponse:
                    succeeded = []
                    failed = []
                    for id_ in ids:
                        try:
                            del self.store[id_]
                        except Exception:
                            failed.append(id_)
                        else:
                            succeeded.append(id_)
                    return DeleteResponse(succeeded=succeeded, failed=failed)

                def lazy_get_by_ids(self, ids: Iterable[str]) -> Iterable[Document]:
                    for id in ids:
                        yield self.store[id]

                def yield_keys(
                    self, *, prefix: Optional[str] = None
                ) -> Union[Iterator[str]]:
                    prefix = prefix or ""
                    for key in self.store:
                        if key.startswith(prefix):
                            yield key
    """  # noqa: E501

    @abstractmethod
    def upsert_by_vector(
        self,
        # TODO: Iterable or Iterator?
        documents: Iterable[Document],
        vectors: Iterable[Vector],
        *,
        ids: Optional[Iterable[str]] = None,
        **kwargs: Any,
    ) -> UpsertResponse:
        """Upsert documents to index."""

    @abstractmethod
    def delete_by_ids(self, ids: Iterable[str]) -> DeleteResponse:
        """Delete documents by id.

        Args:
            ids: IDs of the documents to delete.

        Returns:
           A dict ``{"succeeded": [...], "failed": [...]}`` with the IDs of the
           documents that were successfully deleted and the ones that failed to be
           deleted.
        """

    @abstractmethod
    def lazy_get_by_ids(self, ids: Iterable[str]) -> Iterable[Document]:
        """Lazily get documents by id.

        Args:
            ids: IDs of the documents to get.

        Yields:
           Document
        """

    # FOR CONTRIBUTORS: Overwrite this in Index child classes that support native async get.
    async def alazy_get_by_ids(
        self, ids: AsyncIterable[str]
    ) -> AsyncIterable[Document]:
        """Lazily get documents by id.

        Default implementation, runs sync () in async executor.

        Args:
            ids: IDs of the documents to get.

        Yields:
           Document
        """
        return await run_in_executor(None, self.lazy_get_by_ids, ids)

    def get_by_ids(self, ids: Iterable[str]) -> List[Document]:
        """Get documents by id.

        Args:
            ids: IDs of the documents to get.

        Returns:
           A list of the requested Documents.
        """
        return list(self.lazy_get_by_ids(ids))

    async def aget_by_ids(self, ids: AsyncIterable[str]) -> List[Document]:
        docs = []
        async for doc in await self.alazy_get_by_ids(ids):
            docs.append(doc)
        return docs

    def delete_by_filter(
        self,
        *,
        filters: Union[
            StructuredQuery, Dict[str, Any], List[Dict[str, Any]], None
        ] = None,
        **kwargs: Any,
    ) -> DeleteResponse:
        """Default implementation only supports deletion by id.

        Override this method if the integration supports deletion by other parameters.

        Args:
            ids: IDs of the documents to delete. Must be specified.
            **kwargs: Other keywords args not supported by default. Will be ignored.

        Returns:
           A dict ``{"succeeded": [...], "failed": [...]}`` with the IDs of the
           documents that were successfully deleted and the ones that failed to be
           deleted.

        Raises:
            ValueError: if ids are not provided.
        """
        if ids is None:
            raise ValueError("Must provide ids to delete.")
        if filters:
            kwargs = {"filters": filters, **kwargs}
        if kwargs:
            warnings.warn(
                "Only deletion by ids is supported for this integration, all other "
                f"arguments are ignored. Received {kwargs=}"
            )
        return self.delete_by_ids(ids)

    async def adelete(
        self,
        *,
        ids: Optional[AsyncIterable[str]] = None,
        filters: Union[
            StructuredQuery, Dict[str, Any], List[Dict[str, Any]], None
        ] = None,
        **kwargs: Any,
    ) -> DeleteResponse:
        """Default implementation only supports deletion by id.

        Override this method if the integration supports deletion by other parameters.

        Args:
            ids: IDs of the documents to delete. Must be specified.
            **kwargs: Other keywords args not supported by default. Will be ignored.

        Returns:
           A dict ``{"succeeded": [...], "failed": [...]}`` with the IDs of the
           documents that were successfully deleted and the ones that failed to be
           deleted.

        Raises:
            ValueError: if ids are not provided.
        """
        if ids is None:
            raise ValueError("Must provide ids to delete.")
        if filters:
            kwargs = {"filters": filters, **kwargs}
        if kwargs:
            warnings.warn(
                "Only deletion by ids is supported for this integration, all other "
                f"arguments are ignored. Received {kwargs=}"
            )
        return await self.adelete_by_ids(ids)

    def lazy_get(
        self,
        *,
        ids: Optional[Iterable[str]] = None,
        filters: Union[
            StructuredQuery, Dict[str, Any], List[Dict[str, Any]], None
        ] = None,
        **kwargs: Any,
    ) -> Iterable[Document]:
        """Default implementation only supports get by id.

        Override this method if the integration supports get by other parameters.

        Args:
            ids: IDs of the documents to get. Must be specified.
            **kwargs: Other keywords args not supported by default. Will be ignored.

        Yields:
           Document.

        Raises:
            ValueError: if ids are not provided.
        """
        if ids is None:
            raise ValueError("Must provide ids to get.")
        if filters:
            kwargs = {"filters": filters, **kwargs}
        if kwargs:
            warnings.warn(
                "Only deletion by ids is supported for this integration, all other "
                f"arguments are ignored. Received {kwargs=}"
            )
        return self.lazy_get_by_ids(ids)

    async def alazy_get(
        self,
        *,
        ids: Optional[AsyncIterable[str]] = None,
        filters: Union[
            StructuredQuery, Dict[str, Any], List[Dict[str, Any]], None
        ] = None,
        **kwargs: Any,
    ) -> AsyncIterable[Document]:
        """Default implementation only supports get by id.

        Override this method if the integration supports get by other parameters.

        Args:
            ids: IDs of the documents to get. Must be specified.
            **kwargs: Other keywords args not supported by default. Will be ignored.

        Yields:
           Document.

        Raises:
            ValueError: if ids are not provided.
        """
        if ids is None:
            raise ValueError("Must provide ids to get.")
        if filters:
            kwargs = {"filters": filters, **kwargs}
        if kwargs:
            warnings.warn(
                "Only deletion by ids is supported for this integration, all other "
                f"arguments are ignored. Received {kwargs=}"
            )
        return await self.alazy_get_by_ids(ids)

    def get(
        self,
        *,
        ids: Optional[Iterable[str]] = None,
        filters: Union[
            StructuredQuery, Dict[str, Any], List[Dict[str, Any]], None
        ] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Default implementation only supports get by id.

        Override this method if the integration supports get by other parameters.

        Args:
            ids: IDs of the documents to get. Must be specified.
            **kwargs: Other keywords args not supported by default. Will be ignored.

        Returns:
           A list of the requested Documents.

        Raises:
            ValueError: if ids are not provided.
        """
        return list(self.lazy_get(ids=ids, filters=filters, **kwargs))

    async def aget(
        self,
        *,
        ids: Optional[AsyncIterable[str]] = None,
        filters: Union[
            StructuredQuery, Dict[str, Any], List[Dict[str, Any]], None
        ] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Default implementation only supports get by id.

        Override this method if the integration supports get by other parameters.

        Args:
            ids: IDs of the documents to get. Must be specified.
            **kwargs: Other keywords args not supported by default. Will be ignored.

        Returns:
           A list of the requested Documents.

        Raises:
            ValueError: if ids are not provided.
        """
        docs = []
        async for doc in await self.alazy_get(ids=ids, filters=filters, **kwargs):
            docs.append(doc)
        return docs
