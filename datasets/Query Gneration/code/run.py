from QueryGenerator import*
if __name__ == "__main__":
   
   final_jsonl_file_path = 'C:/Users/b-qixinma/Desktop/UniveralToolKits/Result/4o-08-06/passedTest.jsonl'
   query_path = 'C:/Users/b-qixinma/Desktop/UniveralToolKits/Result/4o-08-06/queries00.jsonl'
   final_path = 'C:/Users/b-qixinma/Desktop/UniveralToolKits/Result/4o-08-06/final00.jsonl'
   generate_queries_for_industries_02(final_jsonl_file_path)
   split_queries(query_path,final_path,0)

