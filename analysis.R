
rm(list=ls())

library(dplyr)
library(jsonlite)
library(purrr)
library(lubridate)
library(tidyr)
library(readr)
library(RODBC)

setwd("GitHub/parse_calendar")
system('python parse_calendar.py --from 2010 --to 2030') #Parse Website

json <- read_json("data.json", simplifyVector = TRUE)

json_sub <- json[['Bern']]

extract_date <- function(df) {
  df %>% mutate(Year = year(Date) %>% as.numeric,
                Month = month(Date) %>% as.numeric,
                Day = day(Date) %>% as.numeric,
                Wday = wday(Date) %>% as.numeric)
}

vacation <- map_df(json_sub, function(x) as.data.frame(x)) %>%
  transmute(Date = ymd(V7), Desc = V8) %>% 
  extract_date() %>% 
  group_by(Year, Month) %>% 
  summarise(Vacations = n()) %>% 
  ungroup()


# dummy dates sequence
dates <- seq(from=ymd('2010-01-01'),
             to=ymd('2040-01-01'),
             by='day') %>% 
  data.frame(Date = .) %>% 
  extract_date() %>% 
  filter(!(Wday %in% c(1,7)))


wdays <- dates %>%
  group_by(Year, Month) %>%
  summarise(Count = n()) %>% 
  ungroup() %>% 
  left_join(vacation, by = c("Year", "Month")) %>% 
  tidyr::replace_na(list(Vacations = 0)) %>% 
  mutate(Wdays = Count - Vacations) %>% 
  select(Year, Month, Wdays)


select <- "SELECT Month,
              Year,
              [name05] Costcenter,
              Sales = sum(Sales)
            FROM [PowerBI].[dbo].[Sales] x
            LEFT JOIN [dbo].[Item] i on i.idClient = x.idClient and x.idItem = i.idItem
            LEFT JOIN [dbo].[Costcenter] co on co.idCostcenter = x.idCostcenterPOS and co.idClient = x.idClient
            GROUP BY Month, Year, [name05]"


dbhandle <- odbcDriverConnect('driver={SQL Server};server=CRHBUSADWH02;database=PowerBI;trusted_connection=true')
df <- sqlQuery(dbhandle, select)

# df_bak <- df
# df <- df_bak

df <- df %>% 
  left_join(wdays, by = c("Month", "Year")) %>% 
  group_by(Year, Costcenter) %>% 
  mutate(Sales_Full_Year = sum(Sales)) %>% 
  ungroup() %>% 
  mutate(Relative = Sales / Sales_Full_Year) %>% 
  filter(Year != year(now())) %>% 
  na.omit()


by_costcenter <- df %>%
  group_by(Costcenter) %>%
  nest()


lmodel <- function(df){
  df <- df %>% mutate(Month = Month %>% as.factor)
  lm(Relative~Month+Wdays, data = df)
}


by_costcenter <- by_costcenter %>% 
  mutate(model = data %>% map(lmodel))



year_to_predict = 2017



new.data <- wdays %>%
  filter(Year == year_to_predict) %>%
  mutate(Month = Month %>% as.factor)


predict_map <- function(model, new.data){
  pred <- predict(model, new.data)
  new.data %>% mutate(prediction = pred)
}

by_costcenter <- by_costcenter %>% 
  mutate(predict = model %>% map(predict_map, new.data),
         glance = model %>% map(broom::glance),
         augment = model %>% map(broom::augment),
         r.squared = glance %>% map_dbl("r.squared"))


normalize_to1 <- function(x, total) x / total

unnested <- by_costcenter %>%
  select(Costcenter, predict, r.squared) %>%
  unnest() %>% 
  group_by(Costcenter) %>% 
  mutate(total = sum(prediction)) %>% 
  ungroup() %>% 
  mutate(prediciton = normalize_to1(prediction, total)) %>% 
  ungroup()



output <- unnested %>%
  filter(!grepl("log", tolower(Costcenter)))



# Output
output %>% write_tsv("phasing.tsv")











