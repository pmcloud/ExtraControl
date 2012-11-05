@echo off

echo ^<test^>

for %%a in (%*) do (
    echo ^<arg^>%%a^</arg^>
)

echo ^</test^>
