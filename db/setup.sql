begin;

/* Create fields table */
drop table if exists fields;
create table fields(
	id integer primary key,
	name text not null,
	good_value real,
	bad_value real
	);

/* Populate fields for test 1 */
insert into fields (id, name, good_value)
values
	(1, "Current assets", 590.3),
	(2, "Cash and cash equivalents", 226.2),
	(3, "Trade receivables and other", 143.0),
	(4, "Income tax receivable", 109.3),
	(5, "Total current assets", 1068.8),
	(6, "Other receivable", 2.0),
	(7, "Deferred tax assets", 58.3),
	(8, "Intangible assets", 1488.1),
	(9, "Property, plant and equipment", 2514.2),
	(10, "Deferred tax liabilities", 552.4),
	(11, "Long-term debt", 9602.9),
	(12, "Total non-current liabilities", 10157.9),
	(13, "Issued capital", 804.6),
	(14, "Total liabilities and equity", 5655.4);

/* Create tests table */
drop table if exists tests;
create table tests(
	id integer primary key,
	test_id integer,
	field_id integer,
	foreign key(field_id) references fields(id),
	unique(test_id, field_id) on conflict replace
	);

/* Populate tests fields */
insert into tests (test_id, field_id)
select 1, id
from fields;

commit;