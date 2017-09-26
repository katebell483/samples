package com.co.etl.shares

import com.co.etl.Boot._
import com.co.etl.util.{ AlertEmailer, ApplicationProperties }
import com.co.etl.{ SqsSource, Etl }
import awscala.sqs.Message

case class Share(gifId: String, userId: Option[Long], shareType: String, eventDate: String)
case class QueueData(name: String, limit: Int)

trait ShareSqsSource extends SqsSource with ApplicationProperties {
  import properties._
  override def queueName = $("sqs.share.queue")
  override def batchLimit = $("sqs.share.batch.limit").toInt
}

object ShareEtl extends ShareSqsSource with ApplicationProperties {
  val etl = new Etl(ShareExtractor, ShareTransformer, ShareLoader, par = true)
  def apply() = while (true) {
    try {
      etl.apply(batchLimit)
    } catch {
      case t: Throwable =>
        AlertEmailer.send("analytics-etl failure", t, "api@co.com")
        logger.error(usage(t.getMessage), t)
    }
  }
}