package com.co.etl.shares

import awscala.sqs.Message
import com.co.etl._
import com.co.etl.util.Logging
import com.google.gson.JsonParser

object ShareTransformer extends ShareTransformer

trait ShareTransformer extends Transformer[Message, (Share, Message)] with Logging {
  override def transform(message: Message): (Share, Message) = {
    val json = new JsonParser().parse(message.getBody).getAsJsonObject
    val userId = json.get("user_id").getAsString
    (Share(
      imgId = json.get("img_id").getAsString,
      userId = if (userId == "") None else Some(userId.toLong),
      shareType = json.get("share_type").getAsString,
      eventDate = json.get("event_time").getAsString),
      message)
  }
}