begin;

/* Create fields table */
drop table if exists fields;
create table fields(
	id integer primary key,
	name text not null,
	actual_value real,
	extracted_value real
	);

/* Populate fields for Test 1 */
insert into fields (id, name, actual_value)
values
	(0, "Current assets", 590.3),
	(1, "Cash and cash equivalents", 226.2),
	(2, "Trade receivables and other", 143.0),
	(3, "Income tax receivable", 109.3),
	(4, "Total current assets", 1068.8),
	(5, "Deferred tax assets", 58.3),
	(6, "Intangible assets", 1488.1),
	(7, "Property, plant and equipment", 2514.2),
	(8, "Deferred tax liabilities", 552.4),
	(9, "Long-term debt", 9602.9),
	(10, "Total non-current liabilities", 10157.9),
	(11, "Issued capital", 804.6),
	(12, "Total liabilities and equity", 5655.4);

/* Populate fields for Test 2 */
insert into fields (id, name, actual_value, extracted_value)
values
	(20, "Service", 20956, 20956),
	(21, "Product", 3218, 3218),
	(22, "Operating costs", 13975, 13975),
	(23, "Depreciation", 3660, 3660),
	(24, "Interest expense", 1146, 1146),
	(25, "Impairment of assets", 279, 279),
	(26, "Income taxes", 967, 967),
	(27, "Net earnings", 2926, 2926),
	(28, "Common shareholders", 2716, 2716),
	(29, "Preferred shareholders", 152, 152),
	(30, "Non-controlling interest", 58, 58),
	(31, "Common shareholders", 2716, 2716),
	(32, "Preferred shareholders", 152, 152),
	(33, "Non-controlling interest", 58, 58),
	(34, "Net earnings", 2926, 2926);

/* Create tests table */
drop table if exists tests;
create table tests(
	id integer primary key,
	test_id integer,
	field_id integer,
	foreign key(field_id) references fields(id),
	unique(test_id, field_id) on conflict replace
	);

/* Populate fields for Test 1 */
insert into tests (test_id, field_id)
select 1, id
from fields
where id < 20;

/* Populate fields for Test 2 */
insert into tests (test_id, field_id)
select 2, id
from fields
where id >=20;

commit;