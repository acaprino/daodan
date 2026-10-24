"""Downloads may return only files beneath /uploads. The fixture has immutable virtual files, no symlinks, no concurrent filesystem changes and no network. The requested relative filename is untrusted.
redirect_destination: All outgoing requests must remain on public.example. The virtual transport follows the returned redirect target, with no network; initial and redirected URLs are attacker influenced.
upload_interpretation: Public uploads must never be served as executable HTML. Stored content is rendered using the returned MIME type. Bytes are untrusted; image_transform validates/decodes and emits inert PNG or rejects, including decompression limits.
check_use_binding: An attacker may replace the directory entry between resolve and open. resolver.is_allowed checks the resolved path; open_checked_handle atomically confines and returns the opened allowed descriptor. Pure injected operations, no real filesystem."""

import posixpath
FILES = {'/uploads/photo.txt': b'public', '/private/config.txt': b'private'}
def download(name):
    target = posixpath.normpath(posixpath.join('/uploads', name))
    if posixpath.commonpath(['/uploads', target]) != '/uploads':
        raise PermissionError('outside uploads')
    return FILES[target]


# Scenario redirect_destination
def destination(initial, redirects):
    from urllib.parse import urlparse
    target = redirects.get(initial, initial)
    for url in (initial, target):
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname != 'public.example':
            raise PermissionError('destination')
    return target


# Scenario upload_interpretation
def store_upload(content, image_transform):
    return image_transform(content), 'image/png'


# Scenario check_use_binding
def open_resource(name, resolver):
    return resolver.open_checked_handle(name)
