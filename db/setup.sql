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
insert into fields (name, good_value)
values
	("Current assets", 590.3),
	("Cash and cash equivalents", 226.2),
	("Trade receivables and other", 143.0),
	("Income tax receivable", 109.3),
	("Total current assets", 1068.8),
	("Other receivable", 2.0),
	("Deferred tax assets", 58.3),
	("Intangible assets", 1488.1),
	("Property, plant and equipment", 2514.2),
	("Deferred tax liabilities", 552.4),
	("Long-term debt", 9602.9),
	("Total non-current liabilities", 10157.9),
	("Issued capital", 804.6),
	("Total liabilities and equity", 5655.4);

/* Create tests table */
drop table if exists tests;
create table tests(
	id integer primary key,
	field_id integer,
	foreign key(field_id) references fields(id)
	);

commit;