package com.co.etl.shares

import awscala.sqs.Message
import com.co.etl.util.Logging
import com.co.etl.{ Loader, RedshiftSink }

object ShareLoader extends ShareLoader

trait ShareLoader extends Loader[(Share, Message)]
    with RedshiftSink
    with ShareSql
    with ShareSqsSource
    with Logging {

  override def load(s: (Share, Message)): Unit = {
    drain({ implicit db =>
      blockingWrite(
        insertIntoShareLogTable("img_share_log", s._1.imgId, s._1.userId, s._1.shareType, s._1.eventDate)
      )
      logger.debug(s"Successfully imported $s into Redshift")
    }, onError = logger.error(s"error saving share: $s to redshift"))
    sqs.delete(s._2)
  }
}
