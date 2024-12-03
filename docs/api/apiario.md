FORMAT: 1A
HOST: http://localhost/api/v3/

# ExaFS API v3

ExaFS API allows authorized machines to send commands directly in JSON, without the web forms. 
The commands are validated in the same way as normal rules.

## Authorization [/auth]

+ Cookies
    + x-api-key (string) - API authorization key, generated for machine identified by IPv4 address
   
### Get JWT token [GET]

Machine must get JWT token from the API first, using it's API key. Then the JWT token is used as the x-access-token for authorization of all operations.

+ Request 
    
    + Headers
        
            x-api-key: your_api_key
    
+ Response 200 (application/json)

        {
        "token": "jwt_token_used_for_all_message_auth"
        }


## Rules Collection [/rules]

### List all rules [GET]


+ Request 
    
    + Headers
        
            x-access-token: jwt_auth_token
    

+ Response 200 (application/json)

            {
            "flowspec_ipv4_rw": [
                {
                    "action": "QoS 1 Mbps",
                    "comment": "",
                    "created": "06/06/2018 13:40",
                    "dest": "",
                    "dest_mask": null,
                    "dest_port": "",
                    "expires": "06/06/2018 15:40",
                    "flags": "",
                    "id": 83,
                    "packet_len": "",
                    "protocol": "tcp",
                    "rstate": "active rule",
                    "source": "192.168.1.2",
                    "source_mask": 32,
                    "source_port": "",
                    "user": "root@example.com"
                }
                {
                    "action": "Accept",
                    "comment": "",
                    "created": "06/06/2018 13:40",
                    "dest": "",
                    "dest_mask": null,
                    "dest_port": "",
                    "expires": "06/06/2018 15:40",
                    "flags": "PSH",
                    "id": 78,
                    "packet_len": "",
                    "protocol": "tcp",
                    "rstate": "active rule",
                    "source": "192.168.1.2",
                    "source_mask": 32,
                    "source_port": "",
                    "user": "root@example.com"
                }
            ],
            "flowspec_ipv6_rw": [],
            "rtbh_any_rw": [
                {
                    "comment": "",
                    "community": "2852:666",
                    "created": "06/06/2018 13:40",
                    "expires": "06/06/2018 15:40",
                    "id": 5,
                    "ipv4": "192.168.0.1",
                    "ipv4_mask": 32,
                    "ipv6": "",
                    "ipv6_mask": null,
                    "rstate": "active rule",
                    "user": "root@example.com"
                }
            ],
            "flowspec_ipv4_ro": [],
            "flowspec_ipv6_ro": [],
            "rtbh_any_ro": []
        }

# IPv4 rules [/rules/ipv4]

## Create new rule [POST]

Create new IPv4 rule. 
Valid IPv4 address and mask must be provided either for source or for the destination. 
The address must be from the addres range of authorized user = machine owner.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token
    
    + Body

            {
                "action": 2,
                "protocol": "tcp",
                "source": "192.168.1.2",
                "source_mask": 32,
                "source_port": "",
                "expires": "06/06/2018 15:40",
            }

+ Response 201 (application/json)

    + Body

            {
                "message": "IPv4 Rule saved",
                "rule": {
                    "action": "QoS 1 Mbps",
                    "comment": "",
                    "created": "2018/06/06 11:40",
                    "dest": "",
                    "dest_mask": null,
                    "dest_port": "",
                    "expires": "2018/06/06 15:40",
                    "flags": "",
                    "id": 86,
                    "packet_len": "",
                    "protocol": "tcp",
                    "rstate": "active rule",
                    "source": "192.168.1.2",
                    "source_mask": 32,
                    "source_port": "",
                    "user": "root@example.com"
                }
            }

## IPv4 rule [/rules/ipv4/{rule_id}]

+ Parameters
    + rule_id (int) - Rule ID
   
### Get rule details [GET]

Get single IPv4 rule. Machine owner must have access rights to selected rule.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token
    
    
+ Response 200 (application/json)

        {
                    "action": "QoS 1 Mbps",
                    "comment": "",
                    "created": "2018/06/06 11:40",
                    "dest": "",
                    "dest_mask": null,
                    "dest_port": "",
                    "expires": "2018/06/06 15:40",
                    "flags": "",
                    "id": 86,
                    "packet_len": "",
                    "protocol": "tcp",
                    "rstate": "active rule",
                    "source": "192.168.1.1",
                    "source_mask": 32,
                    "source_port": "",
                    "user": "root@example.com"
                }


### Delete rule [DELETE]

Delete rule. Must be the owner of the record or admin.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token
    
    
+ Response 201 (application/json)

        {
            "message": "rule deleted"
        }


## IPv6 rules  [/rules/ipv6]

### Create new rule [POST]

Create new IPv6 rule. 
Valid IPv6 address and mask must be provided either for source or for the destination. 
The address must be from the addres range of authorized user = machine owner.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token
    
    + Body

            {
                "action": 32,
                "next_header": "tcp",
                "source": "2011:78:1C01:1111::",
                "source_mask": 64,
                "source_port": "",
                "expires": "06/06/2018 15:40"
            }

+ Response 201 (application/json)

    + Body

            {
                "message": "IPv6 Rule saved",
                "rule": {
                    "action": "QoS 1 Mbps",
                    "comment": "",
                    "created": "2018/06/06 11:40",
                    "dest": "",
                    "dest_mask": null,
                    "dest_port": "",
                    "expires": "2018/06/06 15:40",
                    "flags": "",
                    "id": 86,
                    "packet_len": "",
                    "protocol": "tcp",
                    "rstate": "active rule",
                    "source": "192.168.1.1",
                    "source_mask": 32,
                    "source_port": "",
                    "user": "root@example.com"
                }
            }
            
## IPv6 rule [/rules/ipv6/{rule_id}]

+ Parameters
    + rule_id (int) - Rule ID
   
### Get rule details [GET]

Get single IPv6 rule. Machine owner must have access rights to selected rule.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token
    
    
+ Response 200 (application/json)

        {
                    "action": "QoS 1 Mbps",
                    "comment": "",
                    "created": "2018/06/06 11:40",
                    "dest": "",
                    "dest_mask": null,
                    "dest_port": "",
                    "expires": "2018/06/06 15:40",
                    "flags": "",
                    "id": 86,
                    "packet_len": "",
                    "protocol": "tcp",
                    "rstate": "active rule",
                    "source": "192.168.1.1",
                    "source_mask": 32,
                    "source_port": "",
                    "user": "root@example.com"
                }


### Delete rule [DELETE]

Delete rule. Must be the owner of the record or admin.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token
    
    
+ Response 201 (application/json)

        {
            "message": "rule deleted"
        }



## RTBH rules  [/rules/rtbh]

### Create new rule [POST]

Create new RTBH rule. 
Valid IPv6 or IPv4 address and mask must be provided as the source. 
The address must be from the addres range of authorized user = machine owner.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token
    
    + Body

            {
              "community": 2,
              "ipv4": "192.168.2.1",
              "ipv4_mask": 32,
              "expires": "06/06/2018 15:40"
            }

+ Response 201 (application/json)

    + Body

            {
                "message": "RTBH Rule saved",
                "rule": {
                    "comment": "",
                    "community": "RTBH example",
                    "created": "2018/06/06 11:40",
                    "expires": "2018/06/06 15:40",
                    "id": 4,
                    "ipv4": "192.168.2.1",
                    "ipv4_mask": 32,
                    "ipv6": "",
                    "ipv6_mask": null,
                    "rstate": "active rule",
                    "user": "root@example.org"
                }
            }
            
## RTBH rule [/rules/rtbh/{rule_id}]

+ Parameters
    + rule_id (int) - Rule ID
   
### Get rule details [GET]

Get single RTBH rule. Machine owner must have access rights to selected rule.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token
    
    
+ Response 200 (application/json)

        {
            "comment": "",
            "community": "RTBH example",
            "created": "2018/06/06 11:40",
            "expires": "2018/06/06 15:40",
            "id": 4,
            "ipv4": "192.168.2.1",
            "ipv4_mask": 32,
            "ipv6": "",
            "ipv6_mask": null,
            "rstate": "active rule",
            "user": "root@example.org"
        }


### Delete rule [DELETE]

Delete rule. Must be the owner of the record or admin.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token
    
    
+ Response 201 (application/json)

        {
            "message": "rule deleted"
        }



            
## Actions collection [/actions]

### Get All Actions [GET]

List all actions for the user / machine owner.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token

+ Response 200 (application/json)

    + Body 
    
            [
                [
                    1,
                    "QoS 0.1 Mbps"
                ],
                [
                    2,
                    "QoS 1 Mbps"
                ],
                [
                    3,
                    "QoS 10 Mbps"
                ],
                [
                    5,
                    "QoS 100 Mbps"
                ],
                [
                    6,
                    "QoS 500 Mbps"
                ],
                [
                    7,
                    "Discard"
                ],
                [
                    8,
                    "Accept"
                ]
            ]
            
## Communities collection [/communities]
            
### Get All Communities [GET]

List all RTBH communites for the user / machine owner.

+ Request (application/json)
    
    + Headers
        
            x-access-token: jwt_auth_token

+ Response 200 (application/json)

    + Body 
    
        [
            [
                4,
                "RTBH NIX"
            ],
            [
                5,
                "RTBH CESNET only"
            ],
            [
                8,
                "RTBH CESNET + external sites"
            ]
        ]    