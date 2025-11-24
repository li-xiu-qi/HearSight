"""ASR functions package initializer.

Avoid importing heavy/local-specific modules at package import time so
that submodule-level imports (e.g. asr_functions.asr_sentence_segments)
do not accidentally trigger imports for all implementations (local/cloud).
Modules should import submodules directly, e.g.:
    from asr_functions.asr_sentence_segments import process
or rely on providers to import the appropriate submodule lazily.
"""

__all__ = []
