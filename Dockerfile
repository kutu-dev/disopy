# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

FROM python:3.13-alpine

RUN pip install disopy
RUN mkdir -p /config

VOLUME ["/config"]

CMD ["disopy", "-c", "/config"]
