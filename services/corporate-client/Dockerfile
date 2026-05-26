FROM alpine:3.20

RUN apk add --no-cache curl bash

COPY check.sh /usr/local/bin/check.sh
RUN chmod +x /usr/local/bin/check.sh

CMD ["/usr/local/bin/check.sh"]
