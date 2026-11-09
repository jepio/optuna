import weakref

import pytest

from optuna._imports import try_import


def test_try_import_is_successful() -> None:
    with try_import() as imports:
        pass
    assert imports.is_successful()
    imports.check()


def test_try_import_is_successful_other_error() -> None:
    with pytest.raises(NotImplementedError):
        with try_import() as imports:
            raise NotImplementedError
    assert imports.is_successful()  # No imports failed so `imports` is successful.
    imports.check()


def test_try_import_not_successful() -> None:
    with try_import() as imports:
        raise ImportError
    assert not imports.is_successful()
    with pytest.raises(ImportError):
        imports.check()

    with try_import() as imports:
        raise SyntaxError
    assert not imports.is_successful()
    with pytest.raises(ImportError):
        imports.check()


def test_try_import_does_not_retain_caller_frames() -> None:
    class _Object:
        pass

    def caller() -> tuple[object, weakref.ref[_Object]]:
        obj = _Object()
        with try_import() as imports:
            raise ImportError
        return imports, weakref.ref(obj)

    imports, ref = caller()
    # `imports` is still alive, but it must not keep the locals of the caller alive.
    assert ref() is None
    assert imports is not None


def test_try_import_does_not_retain_chained_exceptions() -> None:
    def caller() -> object:
        try:
            raise RuntimeError("handled")
        except RuntimeError:
            with try_import() as imports:
                raise ImportError("import failed") from ValueError("cause")
        return imports

    imports = caller()
    with pytest.raises(ImportError, match="import failed") as excinfo:
        imports.check()  # type: ignore[attr-defined]

    deferred = excinfo.value.__cause__
    assert isinstance(deferred, ImportError)
    assert deferred.__traceback__ is None
    assert deferred.__context__ is None
    assert deferred.__cause__ is None
