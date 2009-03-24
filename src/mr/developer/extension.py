from mr.developer.common import do_checkout
from pprint import pformat
import os
import zc.buildout.easy_install


FAKE_PART_ID = '_mr.developer'


def extension(buildout=None):
    buildout_dir = buildout['buildout']['directory']

    sources_dir = buildout['buildout'].get('sources-dir', 'src')
    if not os.path.isabs(sources_dir):
        sources_dir = os.path.join(buildout_dir, sources_dir)

    sources = {}
    section = buildout.get(buildout['buildout'].get('sources-svn'), {})
    for name, url in section.iteritems():
        if name in sources:
            raise ValueError("The source for '%s' is already set." % name)
        sources[name] = ('svn', url)
    section = buildout.get(buildout['buildout'].get('sources-git'), {})
    for name, url in section.iteritems():
        if name in sources:
            raise ValueError("The source for '%s' is already set." % name)
        sources[name] = ('git', url)

    # do automatic checkout of specified packages
    packages = {}
    auto_checkout = buildout['buildout'].get('auto-checkout', '').split()
    for name in auto_checkout:
        if name in sources:
            kind, url = sources[name]
            packages.setdefault(kind, {})[name] = url
        else:
            raise ValueError("Automatic checkout failed. No source defined for '%s'." % name)
    do_checkout(packages, sources_dir)

    # build the fake part to install the checkout script
    if FAKE_PART_ID in buildout._raw:
        raise ValueError("mr.developer: The buildout already has a '%s' section, this shouldn't happen" % FAKE_PART_ID)
    buildout._raw[FAKE_PART_ID] = dict(
        recipe='zc.recipe.egg',
        eggs='mr.developer',
        arguments='\n%s,\n"%s",\n%s' % (pformat(sources), sources_dir, auto_checkout),
    )
    # append the fake part
    parts = buildout['buildout']['parts'].split()
    parts.append(FAKE_PART_ID)
    buildout['buildout']['parts'] = " ".join(parts)

    # make the develop eggs if the package is checked out and fixup versions
    develop = buildout['buildout'].get('develop', '')
    versions = buildout.get(buildout['buildout'].get('versions'), {})
    develeggs = {}
    for path in develop.split():
        head, tail = os.path.split(path)
        develeggs[tail] = path
    for name in sources:
        if name not in develeggs:
            path = os.path.join(sources_dir, name)
            if os.path.exists(path):
                develeggs[name] = path
                if name in versions:
                    del versions[name]
    if versions:
        zc.buildout.easy_install.default_versions(dict(versions))
    buildout['buildout']['develop'] = "\n".join(develeggs.itervalues())
