# -*- coding: utf-8 -*-

# Copyright (c) 2013-2017, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


"""Pyramid application test package
"""

import os
from ConfigParser import ConfigParser
from webob.acceptparse import Accept

from pyramid import testing
import c2cgeoportal
from c2cgeoportal import tests
from c2cgeoportal.lib import functionality, caching


mapserv_url = "http://mapserver/"
db_url = None

curdir = os.path.dirname(os.path.abspath(__file__))
configfile = os.path.realpath(os.path.join(curdir, "test.ini"))

if os.path.exists(configfile):
    cfg = ConfigParser()
    cfg.read(configfile)
    db_url = cfg.get("test", "sqlalchemy.url")

caching.init_region({"backend": "dogpile.cache.memory"})
config = None


def set_up_common():
    global config
    config = testing.setUp()

    c2cgeoportal.schema = "main"
    c2cgeoportal.srid = 21781
    functionality.FUNCTIONALITIES_TYPES = None

    # if test.in does not exist (because the z3c.recipe.filetemplate
    # part hasn"t been executed) then db_url is None
    if db_url is None:  # pragma: no cover
        return

    # verify that we have a working database connection before going
    # forward
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    engine = create_engine(db_url)
    try:
        engine.connect()
    except OperationalError:  # pragma: no cover
        return

    import sqlahelper
    sqlahelper.add_engine(engine)


def tear_down_common():
    testing.tearDown()

    functionality.FUNCTIONALITIES_TYPES = None

    # if test.in does not exist (because the z3c.recipe.filetemplate
    # part hasn't been executed) then db_url is None
    if db_url is None:  # pragma: no cover
        return

    import sqlahelper
    sqlahelper.reset()

    # verify that we have a working database connection before going
    # forward
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    engine = create_engine(db_url)
    try:
        engine.connect()
    except OperationalError:  # pragma: no cover
        return

    caching.invalidate_region()


def create_default_ogcserver():
    from c2cgeoportal.models import DBSession, OGCServer
    DBSession.query(OGCServer).delete()
    import transaction
    transaction.commit()
    ogcserver = OGCServer(name="__test_ogc_server")
    ogcserver.url = mapserv_url
    ogcserver_external = OGCServer(name="__test_external_ogc_server")
    ogcserver_external.url = mapserv_url + "?external=true&"
    DBSession.add_all([ogcserver, ogcserver_external])
    return ogcserver, ogcserver_external


def create_dummy_request(additional_settings=None, authentication=True, user=None, *args, **kargs):
    if additional_settings is None:
        additional_settings = {}
    from c2cgeoportal.pyramid_ import default_user_validator
    from c2cgeoportal.pyramid_ import create_get_user_from_request
    from c2cgeoportal.lib.authentication import create_authentication
    request = tests.create_dummy_request({
        "mapserverproxy": {
            "default_ogc_server": "__test_ogc_server",
            "external_ogc_server": "__test_external_ogc_server",
        },
        "functionalities": {
            "registered": {},
            "anonymous": {},
            "available_in_templates": []
        },
        "layers": {
            "geometry_validation": True
        }
    }, *args, **kargs)
    request.accept_language = Accept("fr-CH,fr;q=0.8,en;q=0.5,en-US;q=0.3")
    request.registry.settings.update(additional_settings)
    request.referer = "http://example.com/app"
    request.path_info_peek = lambda: "main"
    request.interface_name = "main"
    request.registry.validate_user = default_user_validator
    request.client_addr = None
    if authentication:
        request._get_authentication_policy = lambda: create_authentication({
            "authtkt_cookie_name": "__test",
            "authtkt_secret": "123",
        })
    elif user is not None:
        config.testing_securitypolicy(user)
    request.set_property(
        create_get_user_from_request({"authorized_referers": [request.referer]}),
        name="user",
        reify=True
    )
    return request
