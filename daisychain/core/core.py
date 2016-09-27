from core.tasks import handle_trigger


class Core():

    def handle_trigger(self, channel_name, trigger_type, userid, payload):
        """Queue the incoming trigger and its metadata.

        This method is called by channels when they receive a trigger.

        The Core should put this in a queue that is handled by worker
        threads.

        Args:
            channel_id (int): The calling Channel
            trigger_type (int): as defined in model Trigger.trigger_type
            userid (int): The user to whom the trigger belongs
            payload (dict): A hashmap that can be freely defined by the trigger
               channel. It will be stored in the queue and handed back to the
               trigger channel when calling the get_trigger_inputs() method

        """
        handle_trigger.delay(channel_name, trigger_type, userid, payload)
