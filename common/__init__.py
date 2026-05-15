"""Tipos e utilitários compartilhados entre servidor e proxy."""

from common.protocol import MessageType, decode_line, encode_line

__all__ = ["MessageType", "decode_line", "encode_line"]
