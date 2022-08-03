from google.cloud.pubsub_v1.publisher.client import publisher_client


class GoogleCloudPubsub:
    def __init__(self, project: str, role: str, study_title: str) -> None:
        self.project = project
        self.publisher = publisher_client.PublisherClient()
        self.topic_id = study_title.replace(" ", "").lower() + "-" + "secure-gwas" + role
        self.topic_path = self.publisher.topic_path(self.project, self.topic_id)

    def publish(self, message: str) -> None:
        self.publisher.publish(request={"topic": self.topic_path, "messages": [{"data": message.encode("utf-8")}]})
