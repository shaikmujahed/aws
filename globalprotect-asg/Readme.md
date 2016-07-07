# Global Protect in AWS with autoscaling
NOTE: This solution is not officially supported by Palo Alto Networks.


1.	Global Protect
GlobalProtect allows remote users to access corporate resources and internet resources using the same security policy enforcement as though there were on premises. To provide Next-Generation Security Platform closer to the remote users, GlobalProtect gateways can be deployed in AWS. This allows instantiation of portals and gateways near remote users without the additional cost of infrastructure. 
Leveraging the global presence and built in redundancy provided by AWS, Global Protect can be quickly deployed worldwide where your users are.  Traffic is inspected with the same PAN-OS security as the corporate firewall but in a globally diverse deployment.  The result is security that follows users – even when they are mobile and a better user experience.

2.	GlobalProtect and AutoScaling
Running within the AWS infrastructure provides the ability to scale-out and scale-in on demand. Take the use cases of both planned and unplanned need for dynamic scaling. Planned events such as a conferences or sales kick-offs where lots of users all try to connect to a regional gateway. And unplanned events such as “snowmageddon” where users are snowed in and work from home. Another very common scenario is a surge of users logging on to the gateway at the start of the day and thus a need for a dynamic scale out of gateways (and scale in at the end of the day)

Please refer to the deployment guide for more details on how to launch the template (docs/gp-asg-guide.pdf)
