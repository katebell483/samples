package com.co.etl.shares

import com.co.etl._
import com.co.etl.util.{ ApplicationProperties, Logging }
import slick.driver.PostgresDriver.api._
import slick.jdbc.{ GetResult, PositionedResult }

import scala.collection.JavaConversions._
import scala.collection.mutable

case class ShareCount(imgId: String, shareType: String, count: Int)

object ShareBackfillEtl extends ApplicationProperties {
  val etl = new El(ShareBackfillExtractor, ShareBackfillLoader)

  // This is an ad hoc etl to seed the redis data with share information.
  // If it is necessary to run this again, then it may need revision,
  // in particular the shareTypes list could now be different
  val shareTypes = List(
    "tumblr",
    "pinterest",
    "facebook",
    "twitter",
    "googleplus",
    "instagram",
    "reddit",
    "embed",
    "total"
  )

  def apply() = shareTypes.foreach(etl.apply)
}

object ShareBackfillExtractor extends Extractor[String, Vector[ShareCount]]
    with RedshiftSource
    with ShareBackfillSql
    with Logging {

  override def extract(shareType: String): Iterator[Vector[ShareCount]] = {
    if (shareType == "total")
      blockingRead(fetchCountsForTotal()).grouped(10000)
    else
      blockingRead(fetchCountsByType(shareType)).grouped(10000)
  }
}

object ShareBackfillLoader extends Loader[Vector[ShareCount]]
    with RedisSink
    with Logging {

  override def load(shareCounts: Vector[ShareCount]): Unit = drain { redis =>
    val pipeline = redis.pipelined
    shareCounts.foreach { s =>
      pipeline.hmset(
        "img:%s:metrics".format(s.imgId),
        mutable.Map(s.shareType + "_shares" -> s.count.toString)
      )
    }
    pipeline.sync()
  }
}

trait ShareBackfillSql {
  implicit val getResult = GetResult({ r: PositionedResult =>
    ShareCount(
      imgId = r.nextString(),
      shareType = r.nextString(),
      count = r.nextInt()
    )
  })

  def fetchCountsByType(shareType: String) = sql"""
      SELECT img_id, share_type, COUNT(*)
      FROM img_share_log
      WHERE img_id IS NOT NULL
      AND share_type = $shareType
      GROUP BY 1, 2
      HAVING COUNT(*) > 1;
    """.as[ShareCount]

  def fetchCountsForTotal() = sql"""
      SELECT img_id, 'total', COUNT(*)
      FROM img_share_log
      WHERE img_id IS NOT NULL
      GROUP BY 1
      HAVING COUNT(*) > 1;
    """.as[ShareCount]
}