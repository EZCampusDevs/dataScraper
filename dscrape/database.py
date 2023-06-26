from sqlalchemy import Date, Float, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session as SessionObj
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy import event
from sqlalchemy import (
    Column,
    Table,
    Integer,
    Boolean,
    TIMESTAMP,
    LargeBinary,
    BigInteger,
    BINARY,
    VARCHAR,
    ForeignKey,
)
from sqlalchemy import UniqueConstraint
import os
import datetime

from . import dataUtil
from . import logger


from py_core.db import *
from py_core.db.db_tables import *


class Scrape:
    Scrape_Time = datetime.datetime.now(datetime.timezone.utc)
    Scrape_id = -1


def get_current_scrape():
    if Scrape.Scrape_id != -1:
        return Scrape.Scrape_id

    logger.info("Inserting new scrape")

    session: SessionObj
    with Session().begin() as session:
        result = session.query(TBL_Scrape_History).filter_by(scrape_time=Scrape.Scrape_Time).first()

        if not result:
            result = TBL_Scrape_History(scrape_time=Scrape.Scrape_Time, has_been_indexed=False)

            session.add(result)
            session.flush()

        Scrape.Scrape_id = result.scrape_id

        logger.info(f"Current Scrape ID: {Scrape.Scrape_id}")

        return result.scrape_id


def get_school_id(school_value: str, subdomain: str):
    session: SessionObj
    with Session().begin() as session:
        result = session.query(TBL_School).filter_by(school_unique_value=school_value).first()

        if result is not None:
            return result.school_id

        new_result = TBL_School(school_unique_value=school_value, subdomain=subdomain)
        session.add(new_result)

        session.flush()

        return new_result.school_id


def get_restriction_type_from_str(value: str, session: SessionObj):
    # Try to find the class_type_id for the given value
    restriction_type_id = (
        session.query(TBL_Restriction_Type).filter_by(restriction_type=value).first()
    )

    if restriction_type_id is not None:
        return restriction_type_id.restriction_type_id

    new_class_type = TBL_Restriction_Type(restriction_type=value)
    session.add(new_class_type)

    session.flush()

    return new_class_type.restriction_type_id


def get_class_type_from_str(value: str, session: SessionObj):
    with session.no_autoflush:
        class_type_id = session.query(TBL_Class_Type).filter_by(class_type=value).first()

    if class_type_id is not None:
        return class_type_id.class_type_id

    new_class_type = TBL_Class_Type(class_type=value)
    session.add(new_class_type)

    session.flush()

    return new_class_type.class_type_id


def add_terms(school_id: int, term_ids: list[int], term_descriptions: list[str]):
    if len(term_ids) != len(term_descriptions):
        raise ValueError("term_ids must be the same length as term_descriptions")

    session: SessionObj
    with Session().begin() as session:
        term_ids = [
            add_term_no_transaction(school_id, term_id, term_description, session)
            for term_id, term_description in zip(term_ids, term_descriptions)
        ]

        return term_ids


def add_term_no_transaction(
    school_id: int, real_term_id: int, term_description: str, session: SessionObj
):
    real_term_id = int(real_term_id)
    school_id = int(school_id)

    with session.no_autoflush:
        result = (
            session.query(TBL_Term)
            .filter_by(real_term_id=real_term_id)
            .filter_by(school_id=school_id)
            .first()
        )

    if not result:
        result = TBL_Term(
            real_term_id=real_term_id,
            school_id=school_id,
            term_description=dataUtil.replace_bad_escapes(term_description),
        )

        session.add(result)

        session.flush()

    return result.term_id


def add_courses(term_ids: list[int], course_codes: list[str], course_descriptions: list[str]):
    ids = []

    session: SessionObj
    with Session().begin() as session:
        for term_id, course_code, course_description in zip(
            term_ids, course_codes, course_descriptions
        ):
            result = (
                session.query(TBL_Course)
                .filter_by(term_id=term_id)
                .filter_by(course_code=course_code)
                .first()
            )

            if not result:
                result = TBL_Course(
                    term_id=term_id,
                    course_code=course_code,
                    course_description=dataUtil.replace_bad_escapes(course_description),
                )

                session.add(result)

                session.flush()

            ids.append(result.course_id)

    return ids


def add_course(term_id: int, course_code: str, course_description: str):
    session: SessionObj
    with Session().begin() as session:
        result = (
            session.query(TBL_Course)
            .filter_by(term_id=term_id)
            .filter_by(course_code=course_code)
            .first()
        )

        if not result:
            result = TBL_Course(
                term_id=term_id,
                course_code=course_code,
                course_description=dataUtil.replace_bad_escapes(course_description),
            )

            session.add(result)

            session.flush()

        return result.course_code


def add_course_data(
    school_id: int,
    course_ids: list[int],
    datas: list[dict[str]],
    restrictions: list[dict[str]] = None,
):
    if len(course_ids) != len(datas):
        raise Exception("The length of course_ids must match the length of datas")

    if restrictions and len(restrictions) != len(datas):
        raise Exception("The length of restrictions must match the length of datas")

    if not restrictions:
        restrictions = [None for i in range(len(course_ids))]

    session: SessionObj
    with Session().begin() as session:
        for course_id, data, restriction in zip(course_ids, datas, restrictions):
            # if something goes wrong here it's gonna frick everything up
            class_type_id = get_class_type_from_str(data["scheduleTypeDescription"], session)

            with session.no_autoflush:
                result = (
                    session.query(TBL_Course_Data)
                    .filter_by(course_id=course_id)
                    .filter_by(crn=data["courseReferenceNumber"])
                    .first()
                )

            for c in (
                "campusDescription",
                "courseTitle",
                "instructionalMethodDescription",
                "subjectDescription",
            ):
                data[c] = dataUtil.replace_bad_escapes(data[c])

            if result:
                with session.no_autoflush:
                    if (
                        result.campus_description != data["campusDescription"]
                        or result.course_title != data["courseTitle"]
                        or result.instructional_method_description
                        != data["instructionalMethodDescription"]
                        or result.subject != data["subject"]
                        or result.subject_long != data["subjectDescription"]
                        or result.class_type_id != class_type_id
                    ):
                        logger.info(
                            f"CourseData with course_id={course_id} and crn={data['courseReferenceNumber']} was already in the database! Updating..."
                        )
                        result.scrape_id = get_current_scrape()
                    result.id = data["id"]
                    result.crn = data["courseReferenceNumber"]
                    result.course_title = data["courseTitle"]
                    result.subject = data["subject"]
                    result.subject_long = data["subjectDescription"]
                    result.sequence_number = str(data["sequenceNumber"])
                    result.campus_description = data["campusDescription"]
                    result.class_type_id = class_type_id
                    result.credit_hours = data["creditHours"]
                    result.maximum_enrollment = data["maximumEnrollment"]
                    result.enrollment = data["enrollment"]
                    result.seats_available = data["seatsAvailable"]
                    result.wait_capacity = data["waitCapacity"]
                    result.wait_count = data["waitCount"]
                    result.wait_available = data["waitAvailable"]
                    result.credit_hour_high = data["creditHourHigh"]
                    result.credit_hour_low = data["creditHourLow"]
                    result.open_section = data["openSection"]
                    result.link_identifier = data["linkIdentifier"]
                    result.is_section_linked = data["isSectionLinked"]
                    result.instructional_method = data["instructionalMethod"]
                    result.instructional_method_description = data["instructionalMethodDescription"]
            else:
                result = TBL_Course_Data(
                    # course code
                    course_id=course_id,
                    scrape_id=get_current_scrape(),
                    #
                    # i have no idea what this value means
                    id=data["id"],
                    #
                    # crn / course reference number; this should be an int always
                    crn=data["courseReferenceNumber"],
                    #
                    # Biology II
                    course_title=data["courseTitle"],
                    # BIOL
                    subject=data["subject"],
                    # Biology
                    subject_long=data["subjectDescription"],
                    #
                    # 001, 002, 003...; should always be int
                    sequence_number=str(data["sequenceNumber"]),
                    #
                    # TODO: add a table for campus instead of using a VARCHAR
                    campus_description=data["campusDescription"],
                    #
                    # Lecture, Laborator, Tutorial
                    class_type_id=class_type_id,
                    #
                    credit_hours=data["creditHours"],
                    maximum_enrollment=data["maximumEnrollment"],
                    enrollment=data["enrollment"],
                    seats_available=data["seatsAvailable"],
                    wait_capacity=data["waitCapacity"],
                    wait_count=data["waitCount"],
                    wait_available=data["waitAvailable"],
                    credit_hour_high=data["creditHourHigh"],
                    credit_hour_low=data["creditHourLow"],
                    open_section=data["openSection"],
                    link_identifier=data["linkIdentifier"],
                    is_section_linked=data["isSectionLinked"],
                    instructional_method=data["instructionalMethod"],
                    instructional_method_description=data["instructionalMethodDescription"],
                )
                session.add(result)
                session.flush()

            course_data_id = result.course_data_id

            for faculty in data["faculty"]:
                faculty["displayName"] = dataUtil.replace_bad_escapes(faculty["displayName"])

                _ = faculty["displayName"] + (faculty.get("emailAddress", "") or "")

                banner_id = dataUtil.sha256_of_str(_)

                if isinstance(banner_id, tuple):
                    raise Exception("IT IS SOMEHOW A TUPLE?????")

                with session.no_autoflush:
                    result = session.query(TBL_Faculty).filter_by(banner_id=banner_id).first()

                if not result:
                    result = TBL_Faculty(
                        banner_id=banner_id,
                        instructor_name=faculty["displayName"],
                        instructor_email=faculty["emailAddress"],
                        instructor_rating=0,
                        scrape_id=get_current_scrape(),
                    )

                    session.add(result)
                    session.flush()

                faculty_id = result.faculty_id

                with session.no_autoflush:
                    result = (
                        session.query(TBL_Course_Faculty)
                        .filter_by(course_data_id=course_data_id)
                        .filter_by(faculty_id=faculty_id)
                        .first()
                    )

                if not result:
                    result = TBL_Course_Faculty(
                        course_data_id=course_data_id, faculty_id=faculty_id
                    )

                    session.add(result)

            # session.flush()

            for meeting in data["meetingsFaculty"]:
                useful_data = meeting["meetingTime"]

                crn = useful_data["courseReferenceNumber"]
                real_term_id = dataUtil.parse_int(useful_data["term"])
                if real_term_id == -1:
                    logger.warning(
                        f"Got bad term_id of {useful_data['term']} course_id={course_id} for meeting {meeting}"
                    )
                    continue

                term_id = add_term_no_transaction(
                    school_id, real_term_id, "UNKNOWN AT TIME OF ADDING", session
                )

                start_date = dataUtil.parse_date(useful_data["startDate"])
                end_date = dataUtil.parse_date(useful_data["endDate"])

                if start_date == end_date:
                    time_delta_days = 0
                else:
                    time_delta_days = 7

                to_insert = TBL_Meeting(
                    meeting_hash=b"",
                    course_data_id=course_data_id,
                    crn=crn,
                    term_id=term_id,
                    time_delta=time_delta_days,
                    building=dataUtil.replace_bad_escapes(useful_data["building"]),
                    building_description=dataUtil.replace_bad_escapes(
                        useful_data["buildingDescription"]
                    ),
                    campus=useful_data["campus"],
                    campus_description=dataUtil.replace_bad_escapes(
                        useful_data["campusDescription"]
                    ),
                    meeting_type=useful_data["meetingType"],
                    meeting_type_description=useful_data["meetingTypeDescription"],
                    start_date=start_date,
                    end_date=end_date,
                    begin_time=useful_data["beginTime"],
                    end_time=useful_data["endTime"],
                    days_of_week=dataUtil.get_weekdays_int(useful_data),
                    room=useful_data["room"],
                    category=useful_data["category"],
                    credit_hour_session=useful_data["creditHourSession"],
                    hours_week=useful_data["hoursWeek"],
                    meeting_schedule_type=useful_data["meetingScheduleType"],
                )

                # we need to make our own unique identifier for the meeting
                # so this is it, just all the data i figured was important
                meeting_hash = dataUtil.sha256_of_str(
                    f"{crn}{term_id}{to_insert.building}{to_insert.campus}{to_insert.meeting_type}"
                    f"{to_insert.start_date}{to_insert.end_date}{to_insert.begin_time}{to_insert.end_time}"
                    f"{to_insert.days_of_week}{to_insert.room}"
                )

                to_insert.meeting_hash = meeting_hash

                with session.no_autoflush:
                    result = session.query(TBL_Meeting).filter_by(meeting_hash=meeting_hash).first()

                if not result:
                    session.add(to_insert)

            if restriction:
                add_restriction_nt(course_data_id, restriction, session)

        session.flush()


def add_restriction_nt(
    course_data_id: int, restriction: dict[str, list[dict[str, bool]]], session: SessionObj
):
    for key, value in restriction.items():
        restriction_type_id = get_restriction_type_from_str(key, session)

        for rest in value:
            rest["value"] = dataUtil.replace_bad_escapes(rest["value"])

            result = session.query(TBL_Restriction).filter_by(restriction=rest["value"]).first()

            if not result:
                result = TBL_Restriction(
                    restriction=rest["value"],
                    must_be_in=rest["must_be_in"],
                    restriction_type=restriction_type_id,
                )

                session.add(result)
                session.flush()

            mapping = (
                session.query(TBL_Course_Restriction)
                .filter_by(restriction_id=result.restriction_id)
                .filter_by(course_data_id=course_data_id)
                .first()
            )

            if not mapping:
                mapping = TBL_Course_Restriction(
                    restriction_id=result.restriction_id, course_data_id=course_data_id
                )
                session.add(mapping)
                session.flush()
