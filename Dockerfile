FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 80
EXPOSE 443

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj files and restore dependencies
COPY ["src/Tinisoft.API/Tinisoft.API.csproj", "src/Tinisoft.API/"]
COPY ["src/Tinisoft.Application/Tinisoft.Application.csproj", "src/Tinisoft.Application/"]
COPY ["src/Tinisoft.Domain/Tinisoft.Domain.csproj", "src/Tinisoft.Domain/"]
COPY ["src/Tinisoft.Infrastructure/Tinisoft.Infrastructure.csproj", "src/Tinisoft.Infrastructure/"]
RUN dotnet restore "src/Tinisoft.API/Tinisoft.API.csproj"

# Copy everything else and build
COPY . .
WORKDIR "/src/src/Tinisoft.API"
RUN dotnet build "Tinisoft.API.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Tinisoft.API.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Tinisoft.API.dll"]

