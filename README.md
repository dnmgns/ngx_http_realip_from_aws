## ngx_http_realip_from_aws
###### Keeping NGINX set_real_ip_from (trusted proxies) in sync with latest Amazon IP ranges
The [ngx_http_realip_module](http://nginx.org/en/docs/http/ngx_http_realip_module.html) is used to change the client address and optional port to the one sent in the specified header fields.

In order for that module to trust a proxy, the proxy needs to be within a 'set_real_ip_from' directive specified address/cidr.

The ip-ranges from Amazon might change at any time, therefore it's important to keep the list of trusted proxies in sync with the current ranges when running NGINX with the ngx_http_realip_module behind AWS CloudFront.

Amazon publishes its [current IP address ranges](http://docs.aws.amazon.com/general/latest/gr/aws-ip-ranges.html) in JSON format. 

This script fetches the current IP address ranges from AWS json-file and writes them to a config-file, in order to keep the 'set_real_ip_from' IP ranges directive up to date.

Bob’s your uncle!